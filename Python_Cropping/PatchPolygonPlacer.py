import os
import sys
from pathlib import Path
# QGISの環境設定
qgis_path = r"C:\Program Files\QGIS 3.36.2"
#qgis.coreに繋ぐパス
sys.path.append(r"C:\Program Files\QGIS 3.36.2\apps\qgis\python")
sys.path.append(r"C:\Program Files\QGIS 3.36.2\apps\qgis\python\plugins")

from qgis.core import *
from PyQt5.QtCore import QVariant
import math
import numpy as np

# QGISの初期化
QgsApplication.setPrefixPath(qgis_path, True)

print("QGIS is working")

import qgis.processing
print("qgis.processing is working")

from plugins.processing.core.Processing import Processing
print("plugins.processing.core.Processing is working")

def create_square_polygon(center_point, width, angle):
    """指定された中心点、幅、角度で正方形ポリゴンを作成する"""
    half_width = width / 2
    
    # 正方形の頂点を計算（中心を原点とした場合）
    vertices = [
        QgsPointXY(-half_width, -half_width),
        QgsPointXY(half_width, -half_width),
        QgsPointXY(half_width, half_width),
        QgsPointXY(-half_width, half_width)
    ]
    
    # 回転行列を適用
    cos_angle = math.cos(math.radians(angle))
    sin_angle = math.sin(math.radians(angle))
    
    rotated_vertices = []
    for vertex in vertices:
        x = vertex.x() * cos_angle - vertex.y() * sin_angle
        y = vertex.x() * sin_angle + vertex.y() * cos_angle
        rotated_vertices.append(QgsPointXY(x + center_point.x(), y + center_point.y()))
    
    # ポリゴンを作成
    polygon = QgsGeometry.fromPolygonXY([[vertex for vertex in rotated_vertices]])
    return polygon

def main():
    # QGISアプリケーションの初期化
    qgs = QgsApplication([], True)
    qgs.initQgis()
    
    # Processingフレームワークの初期化
    Processing.initialize()
    
    try:
        # 入力パラメータの設定
        road_layer_path = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\misc\a13_road_centerline.shp"  # 道路中心線のShapefile
        buffer_layer_path = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\misc\roadbuffer_multiwidth_a13_clipped.fgb"  # バッファポリゴンのレイヤー
        
        # 出力ディレクトリの設定
        output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "SquarePatches"))
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"出力ディレクトリを作成しました: {output_folder}")
        
        # 出力パスの作成
        output_path = str(Path(output_folder + "/SquarePatches.fgb"))
        
        # レイヤーの読み込み
        road_layer = QgsVectorLayer(road_layer_path, "Road Centerline", "ogr")
        buffer_layer = QgsVectorLayer(buffer_layer_path, "Buffer", "ogr")
        
        if not road_layer.isValid() or not buffer_layer.isValid():
            raise Exception("レイヤーの読み込みに失敗しました")
        
        # メモリレイヤーを作成（一時的にEPSG:6675を使用）
        square_layer = QgsVectorLayer("Polygon?crs=EPSG:6675", "Squares", "memory")
        square_provider = square_layer.dataProvider()
        
        # 道路中心線をEPSG:6675に再投影
        print("reprojecting road centerline to EPSG:6675...")
        reprojected_road = qgis.processing.run("native:reprojectlayer", {
            'INPUT': road_layer,
            'TARGET_CRS': 'EPSG:6675',
            'OUTPUT': 'memory:'
        })['OUTPUT']
        
        print("setting up input layers done")
        print("starting loop for road centerline features...")

        # 道路セグメントごとに処理
        for road_feature in reprojected_road.getFeatures():
            road_geom = road_feature.geometry()
            if not road_geom:
                continue
            
            # 道路の長さと向きを取得
            length = road_geom.length()
            angle = road_geom.angleAtVertex(0) * 180 / math.pi
            
            # 道路の幅を取得（R22_005属性から）
            width_class = road_feature['R22_005']
            width = {
                1: 13,  # 幅員階級1: 13m
                2: 9,   # 幅員階級2: 9m
                3: 5,   # 幅員階級3: 5m
                4: 3    # 幅員階級4: 3m
            }.get(width_class, 5)  # デフォルトは5m
            
            # 正方形を配置
            current_pos = 0
            while current_pos < length:
                # 現在位置の点を取得
                point = road_geom.interpolate(current_pos)
                if not point:
                    break
                
                # 正方形を作成
                square = create_square_polygon(point.asPoint(), width, angle)
                
                # バッファポリゴンとの交差を確認
                for buffer_feature in buffer_layer.getFeatures():
                    if square.intersects(buffer_feature.geometry()):
                        # 交差する場合のみ追加
                        feature = QgsFeature()
                        feature.setGeometry(square)
                        square_provider.addFeatures([feature])
                        break
                
                # 次の位置へ移動（正方形の幅分）
                current_pos += width
        
        print("loop for road centerline finished")
        
        # 変更を保存
        square_layer.updateExtents()
        
        # 一時ファイルに保存
        temp_output = str(Path(output_folder + "/temp_squares.fgb"))
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.driverName = "FlatGeobuf"
        QgsVectorFileWriter.writeAsVectorFormatV3(
            square_layer,
            temp_output,
            QgsProject.instance().transformContext(),
            save_options
        )
        
        # 一時ファイルを読み込み
        temp_layer = QgsVectorLayer(temp_output, "Temp Squares", "ogr")
        
        # EPSG:4612に再投影
        print("reprojecting squares to EPSG:4612...")
        reprojected = qgis.processing.run("native:reprojectlayer", {
            'INPUT': temp_layer,
            'TARGET_CRS': 'EPSG:4612',
            'OUTPUT': output_path
        })['OUTPUT']
        
        # レイヤーを解放
        temp_layer = None
        
        # 一時ファイルを削除（エラーハンドリング付き）
        try:
            if os.path.exists(temp_output):
                os.remove(temp_output)
                print("一時ファイルを削除しました")
        except Exception as e:
            print(f"一時ファイルの削除に失敗しましたが、処理は続行します: {str(e)}")
        
        print(f"正方形ポリゴンを保存しました: {output_path}")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
    
    finally:
        # QGISアプリケーションの終了
        qgs.exitQgis()
        print("qgis app exited")

if __name__ == '__main__':
    main()
    print("program finished")

