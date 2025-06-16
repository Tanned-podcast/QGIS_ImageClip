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
        # 空撮画像のGeoTIFF
        aerial_image_path = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\0105\LargeGeoTIFF\a7.tif" 
        #エリア全域のバッファポリゴンが入ったFGBファイルの絶対パス
        buffer_all_path = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\RoadBuffer_ALLAREA_FGB\RoadBuffer_ALLAREA_10m_北陸地方道路DRM.fgb"
        
        # 出力ディレクトリの設定（絶対パスに変更）
        output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "RoadCrop_GeoTIFF"))
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"出力ディレクトリを作成しました: {output_folder}")

        # 切り取り済みバッファFGBの出力ディレクトリの設定（絶対パスに変更）
        clipped_buffer_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "RoadBuffer_Clipped"))
        if not os.path.exists(clipped_buffer_folder):
            os.makedirs(clipped_buffer_folder)
            print(f"出力ディレクトリを作成しました: {clipped_buffer_folder}")
                
        # 出力パスの作成
        imgname = aerial_image_path.split("\\")[-1].split(".")[0]
        output_path = str(Path(output_folder+"/"+imgname+"_clipped.tif"))
        clipped_buffer_path = str(Path(clipped_buffer_folder+"/"+buffer_all_path.split("\\")[-1].split(".")[0]+"_clipped_by_"+imgname+".fgb"))

        #レイヤーとして読み込む     
        aerial_layer = QgsRasterLayer(aerial_image_path, "Aerial Image")
        if not aerial_layer.isValid():
            raise Exception("空撮画像レイヤーの読み込みに失敗しました")
        
        buffer_all_layer = QgsVectorLayer(buffer_all_path, "FGB", "ogr")
        if not buffer_all_layer.isValid():
            print(f"FGBファイルの読み込みに失敗しました。ファイルパス: {buffer_all_path}")
            print(f"エラー: {buffer_all_layer.error().message()}")
            raise Exception("バッファレイヤーの読み込みに失敗しました")
        
        print("loading input layers done")
        

        
        ##ステップ1：バッファポリゴンをラスターの表示範囲で切り取る
        # ラスター自体の表示範囲（extent）を取得
        extent = aerial_layer.extent()
        xmin = extent.xMinimum()
        xmax = extent.xMaximum()
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()

        # extent を "xmin,xmax,ymin,ymax" の文字列に整形（CRS オプション付き）
        crs = aerial_layer.crs().authid()  # 例： "EPSG:4326"
        ext_str = f"{xmin},{xmax},{ymin},{ymax} [{crs}]"

        try:
            # まず、extentの範囲を確認
            print(f"クリッピング範囲: X({xmin}, {xmax}), Y({ymin}, {ymax})")
            
            # 空撮画像と同じサイズの長方形ポリゴンを含む一時的なレイヤーを作成
            temp_layer = QgsVectorLayer("Polygon?crs=" + buffer_all_layer.crs().authid(), "temp", "memory")
            temp_layer.startEditing()
            
            # クリッピング用の矩形を作成
            rect = QgsGeometry.fromRect(QgsRectangle(xmin, ymin, xmax, ymax))
            feat = QgsFeature()
            feat.setGeometry(rect)
            temp_layer.addFeature(feat)
            temp_layer.commitChanges()
            
            # クリッピング処理
            params = {
                'INPUT': buffer_all_layer,
                'OVERLAY': temp_layer,
                'OUTPUT': "memory:"
            }
            
            print("クリッピング処理を開始します...")
            clipped_result = qgis.processing.run("native:clip", params)['OUTPUT']
            print("クリッピング処理が完了しました")
                
            # メモリの解放
            del temp_layer
            QgsApplication.processEvents()
            
        except Exception as e:
            print(f"クリッピング処理でエラーが発生しました: {str(e)}")
            raise
        


        ##ステップ2:ポリゴンをdissolveでマージ
        try:
            print("\nポリゴンのdissolveを開始します...")
            dissolve_params = {
                'INPUT': clipped_result,
                'FIELD': [],  # フィールドを指定しないことで全ポリゴンをマージ
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
        # ラスタのクリップ
        params = {
            'INPUT': aerial_layer,
            'MASK': dissolved_layer,  # dissolveしたポリゴンを使用
            'CROP_TO_CUTLINE': True,     # マスク範囲で切り抜き
            'KEEP_RESOLUTION': True,     # 解像度を維持
            'ALPHA_BAND': True,          # アルファチャンネルを追加
            'NODATA': 0,                 # デフォルトでは 0 を nodata 値として設定
            'OPTIONS': 'COMPRESS=LZW',   # 圧縮オプションを追加
            'DATA_TYPE': 0,              # 入力データタイプを維持
            'EXTRA': '--config GDAL_CACHEMAX 512',  # GDALのキャッシュサイズを設定
            'OUTPUT': output_path
        }
        
        print("クリッピング処理を開始します...")
        try:
            qgis.processing.run("gdal:cliprasterbymasklayer", params)
            print("クリッピング処理が完了しました")
            
        except Exception as e:
            print(f"クリッピング処理でエラーが発生しました: {str(e)}")
            raise


        ##結果の読み込み（GDALドライバを明示的に指定）
        raster_layer_clipped = QgsRasterLayer(output_path, "clipped_raster", "gdal")
        if not raster_layer_clipped.isValid():
            print(f"ラスターレイヤーの読み込みに失敗しました。ファイルパス: {output_path}")
            print(f"エラー: {raster_layer_clipped.error().message()}")
            raise Exception("クリッピング処理に失敗しました")        
        print(f"ラスターレイヤーの読み込みに成功しました。サイズ: {raster_layer_clipped.width()}x{raster_layer_clipped.height()}")
        
        print(f"処理が完了しました。出力ファイル: {output_path}")
    
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
    
    finally:
        # QGISアプリケーションの終了
        qgs.exitQgis()
        print("qgis app exited")

if __name__ == '__main__':
    main()
    print("program ended")
