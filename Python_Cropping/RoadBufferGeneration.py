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
        buffer_width = 0.0001  # バッファの幅（メートル）
        
        # 出力ディレクトリの設定（絶対パスに変更）
        output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "RoadBuffer_ALLAREA_FGB"))
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"出力ディレクトリを作成しました: {output_folder}")        
        
        # 出力パスの作成
        output_path = str(Path(output_folder+"/RoadBuffer_ALLAREA_"+str(buffer_width)+"m_"+road_layer_path.split("\\")[-2]+".fgb" ))
        
        
        # 入力レイヤーの読み込み
        road_layer = QgsVectorLayer(road_layer_path, "Road Centerline", "ogr")
        if not road_layer.isValid():
            raise Exception("道路中心線レイヤーの読み込みに失敗しました")        
        print("loading input layers done")
        
        ##ステップ1:バッファの作成
        params = {
            'INPUT': road_layer,
            'DISTANCE': buffer_width,
            'SEGMENTS': 5,
            'END_CAP_STYLE': 0,
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'DISSOLVE': True,
            'OUTPUT': output_path
        }
        
        qgis.processing.run("native:buffer", params)
        print("buffer polygon is generated")

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
    
    finally:
        # QGISアプリケーションの終了
        qgs.exitQgis()

if __name__ == '__main__':
    main()
        