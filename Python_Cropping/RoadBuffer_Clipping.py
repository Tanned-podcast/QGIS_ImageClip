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


def process_single_image(aerial_image_path, buffer_all_path, output_folder, clipped_buffer_folder):
    """単一の画像に対する処理を実行する関数"""
    try:
        # 出力パスの作成
        imgname = aerial_image_path.split("\\")[-1].split(".")[0]
        output_path = str(Path(output_folder+"/"+imgname+"_clipped.tif"))
        clipped_buffer_path = str(Path(clipped_buffer_folder+"/"+buffer_all_path.split("\\")[-1].split(".")[0]+"_clipped_by_"+imgname+".fgb"))

        #レイヤーとして読み込む     
        aerial_layer = QgsRasterLayer(aerial_image_path, "Aerial Image")
        if not aerial_layer.isValid():
            raise Exception(f"空撮画像レイヤーの読み込みに失敗しました: {aerial_image_path}")
        
        buffer_all_layer = QgsVectorLayer(buffer_all_path, "FGB", "ogr")
        if not buffer_all_layer.isValid():
            print(f"FGBファイルの読み込みに失敗しました。ファイルパス: {buffer_all_path}")
            print(f"エラー: {buffer_all_layer.error().message()}")
            raise Exception("バッファレイヤーの読み込みに失敗しました")
        
        print(f"画像 {imgname} の処理を開始します...")
        
        ##ステップ1：バッファポリゴンをラスターの表示範囲で切り取る
        extent = aerial_layer.extent()
        xmin = extent.xMinimum()
        xmax = extent.xMaximum()
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()

        try:
            print(f"クリッピング範囲: X({xmin}, {xmax}), Y({ymin}, {ymax})")
            
            temp_layer = QgsVectorLayer("Polygon?crs=" + buffer_all_layer.crs().authid(), "temp", "memory")
            temp_layer.startEditing()
            
            rect = QgsGeometry.fromRect(QgsRectangle(xmin, ymin, xmax, ymax))
            feat = QgsFeature()
            feat.setGeometry(rect)
            temp_layer.addFeature(feat)
            temp_layer.commitChanges()
            
            params = {
                'INPUT': buffer_all_layer,
                'OVERLAY': temp_layer,
                'OUTPUT': "memory:"
            }
            
            print("クリッピング処理を開始します...")
            clipped_result = qgis.processing.run("native:clip", params)['OUTPUT']
            print("クリッピング処理が完了しました")
                
            del temp_layer
            QgsApplication.processEvents()
            
        except Exception as e:
            print(f"クリッピング処理でエラーが発生しました: {str(e)}")
            raise

        ##ステップ2:ポリゴンをdissolveでマージ
        try:
            print("ポリゴンのdissolveを開始します...")
            dissolve_params = {
                'INPUT': clipped_result,
                'FIELD': [],
                'OUTPUT': clipped_buffer_path
            }
            qgis.processing.run("native:dissolve", dissolve_params)
            dissolved_layer = QgsVectorLayer(clipped_buffer_path, "dissolved", "ogr")
            if not dissolved_layer.isValid():
                raise Exception("dissolve処理に失敗しました")
        except Exception as e:
            print(f"dissolve処理でエラーが発生しました: {str(e)}")
            raise

        print("ポリゴンのdissolveが完了しました")

        ##ステップ3:ラスター画像を小さなバッファポリゴンで切り取る
        params = {
            'INPUT': aerial_layer,
            'MASK': dissolved_layer,
            'CROP_TO_CUTLINE': True,
            'KEEP_RESOLUTION': True,
            'ALPHA_BAND': True,
            'NODATA': 0,
            'OPTIONS': 'COMPRESS=LZW',
            'DATA_TYPE': 0,
            'EXTRA': '--config GDAL_CACHEMAX 512',
            'OUTPUT': output_path
        }
        
        print("クリッピング処理を開始します...")
        try:
            qgis.processing.run("gdal:cliprasterbymasklayer", params)
            print("クリッピング処理が完了しました")
            
        except Exception as e:
            print(f"クリッピング処理でエラーが発生しました: {str(e)}")
            raise

        raster_layer_clipped = QgsRasterLayer(output_path, "clipped_raster", "gdal")
        if not raster_layer_clipped.isValid():
            print(f"ラスターレイヤーの読み込みに失敗しました。ファイルパス: {output_path}")
            print(f"エラー: {raster_layer_clipped.error().message()}")
            raise Exception("クリッピング処理に失敗しました")        
        print(f"ラスターレイヤーの読み込みに成功しました。サイズ: {raster_layer_clipped.width()}x{raster_layer_clipped.height()}")
        
        print(f"画像 {imgname} の処理が完了しました。出力ファイル: {output_path}")
        return True

    except Exception as e:
        print(f"画像 {imgname} の処理中にエラーが発生しました: {str(e)}")
        return False


def main():
    # QGISアプリケーションの初期化
    qgs = QgsApplication([], True)
    qgs.initQgis()
    
    # Processingフレームワークの初期化
    Processing.initialize()
    
    try:
        # 入力パスの設定
        aerial_image_folder = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\test_tiff"
        buffer_all_path = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\RoadBuffer_ALLAREA_FGB\RoadBuffer_ALLAREA_10m_北陸地方道路DRM.fgb"
        
        # 出力ディレクトリの設定
        output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "RoadCrop_GeoTIFF"))
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"出力ディレクトリを作成しました: {output_folder}")

        clipped_buffer_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "RoadBuffer_Clipped"))
        if not os.path.exists(clipped_buffer_folder):
            os.makedirs(clipped_buffer_folder)
            print(f"出力ディレクトリを作成しました: {clipped_buffer_folder}")

        # 空撮画像フォルダ内の全画像を処理
        success_count = 0
        error_count = 0
        
        for filename in os.listdir(aerial_image_folder):
            if filename.lower().endswith(('.tif', '.tiff')):
                aerial_image_path = os.path.join(aerial_image_folder, filename)
                if process_single_image(aerial_image_path, buffer_all_path, output_folder, clipped_buffer_folder):
                    success_count += 1
                else:
                    error_count += 1

        print(f"\n処理完了: 成功 {success_count} 件, 失敗 {error_count} 件")
    
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
    
    finally:
        # QGISアプリケーションの終了
        qgs.exitQgis()
        print("qgis app exited")

if __name__ == '__main__':
    main()
    print("program ended")
