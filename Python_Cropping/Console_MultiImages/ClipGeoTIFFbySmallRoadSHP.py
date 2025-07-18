#広域空撮GeoTIFFをバッファポリゴンでクリッピング
import processing
from qgis.core import QgsProject
import os

output_dir = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\RoadCrop_GeoTIFF"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# プロジェクト内のすべてのレイヤーを取得
layers = list(QgsProject.instance().mapLayers().values())
raster_layers = [lyr for lyr in layers if lyr.type() == 1]  # 1: RasterLayer
vector_layers = [lyr for lyr in layers if lyr.type() == 0]  # 0: VectorLayer

for raster in raster_layers:
    # ラスターレイヤー名を含むベクターレイヤーを探す
    matching_vectors = [v for v in vector_layers if raster.name() in v.name()]
    if not matching_vectors:
        print(f"ラスターレイヤー「{raster.name()}」に対応するベクターレイヤーが見つかりません。")
        continue
    for mask in matching_vectors:
        output_path = os.path.join(output_dir, f"{raster.name()}_clipped.tif")
        params = {
            'INPUT': raster,
            'MASK': mask,
            'CROP_TO_CUTLINE': True,
            'KEEP_RESOLUTION': True,
            'ALPHA_BAND': True,
            'NODATA': 0,
            'OUTPUT': output_path
        }
        processing.run('gdal:cliprasterbymasklayer', params)
        print(f"{raster.name()} を {mask.name()} でクリッピングし保存しました。")

print("全ラスターレイヤーについてクリッピング＆保存が完了しました。")
