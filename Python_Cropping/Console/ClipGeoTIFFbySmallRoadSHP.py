import processing
from qgis.core import QgsProject

rasterlayer_name="a2"
vectorlayer_name="merged_buffer"
output_path=r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\a2_test2.tif"

# 入力ラスター & マスク（ポリゴン）レイヤーを取得
raster = QgsProject.instance().mapLayersByName(rasterlayer_name)[0]
mask = QgsProject.instance().mapLayersByName(vectorlayer_name)[0]

params = {
    'INPUT': raster,
    'MASK': mask,
    'CROP_TO_CUTLINE': True,     # マスク範囲で切り抜き
    'KEEP_RESOLUTION': True,     # 解像度を維持
    'ALPHA_BAND': True,          # アルファチャンネルを追加
    'NODATA': 0,                 # デフォルトでは 0 を nodata 値として設定
    'OUTPUT': output_path
}

res = processing.run('gdal:cliprasterbymasklayer', params)
