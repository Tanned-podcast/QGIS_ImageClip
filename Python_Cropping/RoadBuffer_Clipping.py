print("Start")
import os
import sys

# QGISの環境設定
qgis_path = r"C:\Program Files\QGIS 3.36.2"
#qgis.coreに繋ぐパス
sys.path.append(r"C:\Program Files\QGIS 3.36.2\apps\qgis\python")
sys.path.append(r"C:\Program Files\QGIS 3.36.2\apps\qgis\python\plugins")
#sys.path.append(r"C:\Program Files\QGIS 3.36.2\apps\Python39\Lib\site-packages")
#sys.path.append(r"C:\Program Files\QGIS 3.36.2\apps\qgis\python\qgis\PyQt")
#sys.path.append(r"C:\Program Files\QGIS 3.36.2\apps\Python39\Lib\site-packages\PyQt5\Qt5\bin")


#from PyQt5.QtCore import *
#print("PyQt5 is working")

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
        aerial_image_path = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\0105\LargeGeoTIFF\a5.tif"  # 空撮画像のGeoTIFF
        buffer_width = 10  # バッファの幅（メートル）
        
        # 出力ディレクトリの設定（絶対パスに変更）
        output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "RoadCrop_GeoTIFF"))
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"出力ディレクトリを作成しました: {output_folder}")
        
        output_filename = "clipped_a5.tif"  # 出力ファイル名
        #fgb_path = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\hokuriku_road_buffer.fgb"  # FGBファイルの絶対パス
        
        # 出力パスの作成
        output_path = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\RoadCrop_GeoTIFF\clipped_a5.tif"
        temp_output = os.path.join(output_folder, "buffer_temp.fgb")
        
        print(f"出力ディレクトリ: {output_folder}")
        print(f"一時ファイル: {temp_output}")
        
        """
        # 入力レイヤーの読み込み
        road_layer = QgsVectorLayer(road_layer_path, "Road Centerline", "ogr")
        if not road_layer.isValid():
            raise Exception("道路中心線レイヤーの読み込みに失敗しました")
        """
             
        aerial_layer = QgsRasterLayer(aerial_image_path, "Aerial Image")
        if not aerial_layer.isValid():
            raise Exception("空撮画像レイヤーの読み込みに失敗しました")
        
        """
        fgb_layer = QgsVectorLayer(fgb_path, "FGB", "ogr")
        if not fgb_layer.isValid():
            print(f"FGBファイルの読み込みに失敗しました。ファイルパス: {fgb_path}")
            print(f"エラー: {fgb_layer.error().message()}")
            raise Exception("FGBレイヤーの読み込みに失敗しました")
        
        print("loading input layers done")
        """

        # メモリ使用量を抑えるために、不要なレイヤーを解放
        #del road_layer
        #QgsApplication.processEvents()

        """
        ##ステップ1:バッファの作成
        params = {
            'INPUT': road_layer,
            'DISTANCE': buffer_width,
            'SEGMENTS': 5,
            'END_CAP_STYLE': 0,
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'DISSOLVE': True,
            'OUTPUT': 'memory:buffer'
        }
        
        buffer_result = qgis.processing.run("native:buffer", params)
        buffer_layer = buffer_result['OUTPUT']
        print("buffer polygon is generated")
        """
        
        ##ステップ2：バッファポリゴンをラスターの表示範囲で切り取る
        # ラスター自体の表示範囲（extent）を取得
        extent = aerial_layer.extent()
        xmin = extent.xMinimum()
        xmax = extent.xMaximum()
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()

        # extent を "xmin,xmax,ymin,ymax" の文字列に整形（CRS オプション付き）
        crs = aerial_layer.crs().authid()  # 例： "EPSG:4326"
        ext_str = f"{xmin},{xmax},{ymin},{ymax} [{crs}]"

        print("did not clash till here")

        # 一時ファイルとして出力するように変更
        temp_output = os.path.join(output_folder, "a5_buffer_clipped.gpkg")
        
        # 処理を段階的に実行
        try:
            # まず、extentの範囲を確認
            print(f"クリッピング範囲: X({xmin}, {xmax}), Y({ymin}, {ymax})")
            
            # 一時的なバッファレイヤーを作成
            temp_layer = QgsVectorLayer("Polygon?crs=" + fgb_layer.crs().authid(), "temp", "memory")
            temp_layer.startEditing()
            
            # クリッピング用の矩形を作成
            rect = QgsGeometry.fromRect(QgsRectangle(xmin, ymin, xmax, ymax))
            feat = QgsFeature()
            feat.setGeometry(rect)
            temp_layer.addFeature(feat)
            temp_layer.commitChanges()
            
            # クリッピング処理
            params = {
                'INPUT': fgb_layer,
                'OVERLAY': temp_layer,
                'OUTPUT': temp_output
            }
            
            print("クリッピング処理を開始します...")
            res = qgis.processing.run("native:clip", params)
            print("クリッピング処理が完了しました")
            
            # 結果の読み込み
            buffer_layer_clipped = QgsVectorLayer(temp_output, "clipped", "ogr")
            if not buffer_layer_clipped.isValid():
                raise Exception("クリッピング処理に失敗しました")
                
            # メモリの解放
            del temp_layer
            QgsApplication.processEvents()
            
        except Exception as e:
            print(f"クリッピング処理でエラーが発生しました: {str(e)}")
            raise
        

        fgb_path = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\RoadCrop_GeoTIFF\a5_buffer_clipped.fgb"
        fgb_layer = QgsVectorLayer(fgb_path, "FGB", "ogr")
        if not fgb_layer.isValid():
            print(f"fgbファイルの読み込みに失敗しました。ファイルパス: {fgb_path}")
            print(f"エラー: {fgb_layer.error().message()}")
            raise Exception("fgbレイヤーの読み込みに失敗しました")

        print("fgb layer loaded")
        
        # FGBファイルの範囲を確認
        fgb_extent = fgb_layer.extent()
        print(f"FGBファイルの範囲:")
        print(f"X範囲: {fgb_extent.xMinimum()} から {fgb_extent.xMaximum()}")
        print(f"Y範囲: {fgb_extent.yMinimum()} から {fgb_extent.yMaximum()}")
        print(f"FGBファイルのCRS: {fgb_layer.crs().authid()}")
        
        # 空撮画像の範囲も確認
        aerial_extent = aerial_layer.extent()
        print(f"\n空撮画像の範囲:")
        print(f"X範囲: {aerial_extent.xMinimum()} から {aerial_extent.xMaximum()}")
        print(f"Y範囲: {aerial_extent.yMinimum()} から {aerial_extent.yMaximum()}")
        print(f"空撮画像のCRS: {aerial_layer.crs().authid()}")
        
        # 範囲の重なりを確認
        if fgb_extent.intersects(aerial_extent):
            print("\n範囲が重なっています")
            intersection = fgb_extent.intersect(aerial_extent)
            print(f"重なりの範囲:")
            print(f"X範囲: {intersection.xMinimum()} から {intersection.xMaximum()}")
            print(f"Y範囲: {intersection.yMinimum()} から {intersection.yMaximum()}")
        else:
            print("\n警告: 範囲が重なっていません！")
            print("FGBファイルと空撮画像の範囲が一致していない可能性があります。")

        # FGBファイルのポリゴン情報を確認
        print("\nFGBファイルのポリゴン情報:")
        print(f"ポリゴン数: {fgb_layer.featureCount()}")
        
        # 最初のポリゴンの範囲を確認
        first_feature = next(fgb_layer.getFeatures())
        first_geom = first_feature.geometry()
        first_extent = first_geom.boundingBox()
        print(f"最初のポリゴンの範囲:")
        print(f"X範囲: {first_extent.xMinimum()} から {first_extent.xMaximum()}")
        print(f"Y範囲: {first_extent.yMinimum()} から {first_extent.yMaximum()}")
        
        # 最後のポリゴンの範囲を確認
        features = list(fgb_layer.getFeatures())
        last_feature = features[-1]
        last_geom = last_feature.geometry()
        last_extent = last_geom.boundingBox()
        print(f"最後のポリゴンの範囲:")
        print(f"X範囲: {last_extent.xMinimum()} から {last_extent.xMaximum()}")
        print(f"Y範囲: {last_extent.yMinimum()} から {last_extent.yMaximum()}")

        # ポリゴンをdissolveでマージ
        print("\nポリゴンのdissolveを開始します...")
        dissolve_params = {
            'INPUT': fgb_layer,
            'FIELD': [],  # フィールドを指定しないことで全ポリゴンをマージ
            'OUTPUT': temp_output
        }
        
        try:
            dissolved_result = qgis.processing.run("native:dissolve", dissolve_params)
            dissolved_layer = QgsVectorLayer(temp_output, "dissolved", "ogr")
            
            if not dissolved_layer.isValid():
                raise Exception("dissolve処理に失敗しました")
            
            # dissolveしたポリゴンの範囲を確認
            dissolved_extent = dissolved_layer.extent()
            print(f"dissolve後のポリゴン範囲:")
            print(f"X範囲: {dissolved_extent.xMinimum()} から {dissolved_extent.xMaximum()}")
            print(f"Y範囲: {dissolved_extent.yMinimum()} から {dissolved_extent.yMaximum()}")
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
                res_3 = qgis.processing.run("gdal:cliprasterbymasklayer", params)
                print("クリッピング処理が完了しました")
                
                # 結果の読み込み（GDALドライバを明示的に指定）
                raster_layer_clipped = QgsRasterLayer(output_path, "clipped_raster", "gdal")
                if not raster_layer_clipped.isValid():
                    print(f"ラスターレイヤーの読み込みに失敗しました。ファイルパス: {output_path}")
                    print(f"エラー: {raster_layer_clipped.error().message()}")
                    raise Exception("クリッピング処理に失敗しました")
                
                print(f"ラスターレイヤーの読み込みに成功しました。サイズ: {raster_layer_clipped.width()}x{raster_layer_clipped.height()}")
                
            except Exception as e:
                print(f"クリッピング処理でエラーが発生しました: {str(e)}")
                raise
            
            print(f"処理が完了しました。出力ファイル: {output_path}")
            
        except Exception as e:
            print(f"dissolve処理でエラーが発生しました: {str(e)}")
            raise
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
    
    finally:
        # QGISアプリケーションの終了
        qgs.exitQgis()

if __name__ == '__main__':
    main()
