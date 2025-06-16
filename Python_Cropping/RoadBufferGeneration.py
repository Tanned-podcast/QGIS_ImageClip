import os
import sys
from pathlib import Path
# QGISの環境設定
qgis_path = r"C:\Program Files\QGIS 3.36.2"
#qgis.coreに繋ぐパス
sys.path.append(r"C:\Program Files\QGIS 3.36.2\apps\qgis\python")
sys.path.append(r"C:\Program Files\QGIS 3.36.2\apps\qgis\python\plugins")


from qgis.core import *
# QGISの初期化
QgsApplication.setPrefixPath(qgis_path, True)

print("QGIS is working")

import qgis.processing
print("qgis.processing is working")

from plugins.processing.core.Processing import Processing
print("plugins.processing.core.Processing is working")


def main():
    # QGISアプリケーションの初期化
    qgs = QgsApplication([], True)
    qgs.initQgis()
    
    # Processingフレームワークの初期化
    Processing.initialize()
    
    try:
        # 入力パラメータの設定
        road_layer_path = r"C:\Users\kyohe\北陸地方道路DRM\全道路リンク標高.shp"  # 道路中心線のShapefile
        
        # 幅員階級ごとのバッファ幅の設定
        buffer_widths = {
            1: 13,  # 幅員階級1: 13m
            2: 9,   # 幅員階級2: 9m
            3: 5,   # 幅員階級3: 5m
            4: 3    # 幅員階級4: 3m
        }
        
        # 出力ディレクトリの設定（絶対パスに変更）
        output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "RoadBuffer_ALLAREA_FGB"))
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"出力ディレクトリを作成しました: {output_folder}")        
        
        # 出力パスの作成
        output_path = str(Path(output_folder+"/RoadBuffer_ALLAREA_MultiWidth_"+road_layer_path.split("\\")[-1].split(".")[0]+".fgb"))
        
        # 入力レイヤーの読み込み
        road_layer = QgsVectorLayer(road_layer_path, "Road Centerline", "ogr")
        if not road_layer.isValid():
            raise Exception("道路中心線レイヤーの読み込みに失敗しました")        
        print("loading input layers done")

        #バッファ処理をメートル単位でするためにはEPSG4612ではダメ：日本測地系2011の7系に直す
        #再投影するCRSの設定
        original_crs = road_layer.crs().authid()
        temp_crs = 'EPSG:6675'
        

        # 再投影（メートル投影系へ）　CRSのDBにアクセスできませんっていうエラー出るけど正常に動くので問題なし
        print("reprojecting roadline...")
        reproj = qgis.processing.run("native:reprojectlayer", {
            'INPUT': road_layer,
            'TARGET_CRS': temp_crs,
            'OUTPUT': 'memory:'
        })['OUTPUT']
        print("roadline reprojected")

        # 幅員階級ごとにバッファを生成
        buffer_layers = []
        for width_class, buffer_width in buffer_widths.items():
            print(f"幅員階級 {width_class} のバッファを生成中...")
            
            # 幅員階級でフィルタリング
            expression = f'"R22_005" = {width_class}'
            filtered = qgis.processing.run("native:extractbyexpression", {
                'INPUT': reproj,
                'EXPRESSION': expression,
                'OUTPUT': 'memory:'
            })['OUTPUT']
            
            # バッファ処理
            buf = qgis.processing.run("native:buffer", {
                'INPUT': filtered,
                'DISTANCE': buffer_width,
                'SEGMENTS': 5,
                'END_CAP_STYLE': 0,
                'JOIN_STYLE': 0,
                'MITER_LIMIT': 2,
                'DISSOLVE': False,
                'OUTPUT': 'memory:'
            })['OUTPUT']
            
            buffer_layers.append(buf)
            print(f"幅員階級 {width_class} のバッファ生成完了")

        # バッファレイヤーをマージ
        print("バッファレイヤーをマージ中...")
        merged = qgis.processing.run("native:mergevectorlayers", {
            'LAYERS': buffer_layers,
            'OUTPUT': 'memory:'
        })['OUTPUT']

        # 再投影（EPSG:4612 に戻す）
        print("reprojecting buffer...")
        final = qgis.processing.run("native:reprojectlayer", {
            'INPUT': merged,
            'TARGET_CRS': original_crs,
            'OUTPUT': output_path
        })['OUTPUT']
        print("buffer reprojected")

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
    
    finally:
        # QGISアプリケーションの終了
        qgs.exitQgis()
        print("qgis app exited")

if __name__ == '__main__':
    main()
    print("program finished")