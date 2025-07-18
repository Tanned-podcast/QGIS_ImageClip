#DRM道路線を広域空撮の範囲でクリッピング（計算軽くする），切り取った各DRM線に対してバッファ生成&マージ
from qgis.core import QgsProject, QgsVectorLayer
import processing
import os
from qgis.core import QgsVectorFileWriter
import math

# 保存先ディレクトリ
output_dir = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\RoadBuffer_Clipped"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

vectorlayer_name = "DRM_edited"
vector_layer = QgsProject.instance().mapLayersByName(vectorlayer_name)[0]

# プロジェクト内のすべてのラスターレイヤーを取得
layers = QgsProject.instance().mapLayers().values()
raster_layers = [lyr for lyr in layers if lyr.type() == 1]  # 1: RasterLayer

# バッファ幅の辞書
buffer_widths = {
    1: 37,      # 幅員階級1: 13m
    2: 33.25,   # 幅員階級2: 9m
    3: 28.25,   # 幅員階級3: 5m
    4: 27       # 幅員階級4: 3m
}

for raster_layer in raster_layers:
    # ラスターの範囲取得
    extent = raster_layer.extent()
    xmin = extent.xMinimum()
    xmax = extent.xMaximum()
    ymin = extent.yMinimum()
    ymax = extent.yMaximum()
    crs = raster_layer.crs().authid()
    ext_str = f"{xmin},{xmax},{ymin},{ymax} [{crs}]"

    # クリップ処理
    params = {
        'INPUT': vector_layer,
        'EXTENT': ext_str,
        'CLIP': True,
        'OUTPUT': 'memory:'
    }
    res = processing.run("qgis:extractbyextent", params)
    clipped_layer = res['OUTPUT']

    # 1. バッファ生成前にEPSG:6675へ再投影
    original_crs = clipped_layer.crs().authid()
    temp_crs = 'EPSG:6675'
    reproj = processing.run("native:reprojectlayer", {
        'INPUT': clipped_layer,
        'TARGET_CRS': temp_crs,
        'OUTPUT': 'memory:'
    })['OUTPUT']

    # 2. R22_005ごとにバッファ生成
    buffer_layers = []
    for width_class, buffer_width in buffer_widths.items():
        expression = f'"R22_005" = {width_class}'
        filtered = processing.run("native:extractbyexpression", {
            'INPUT': reproj,
            'EXPRESSION': expression,
            'OUTPUT': 'memory:'
        })['OUTPUT']

        # バッファ幅を調整
        buffer_width = buffer_width * math.sqrt(2) / 2
        buf = processing.run("native:buffer", {
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

    # 3. バッファレイヤをマージ
    merged = processing.run("native:mergevectorlayers", {
        'LAYERS': buffer_layers,
        'OUTPUT': 'memory:'
    })['OUTPUT']

    # 4. 元のCRSに戻す
    final = processing.run("native:reprojectlayer", {
        'INPUT': merged,
        'TARGET_CRS': original_crs,
        'OUTPUT': 'memory:'
    })['OUTPUT']

    # 5. dissolveで全ポリゴンを1つにまとめる
    dissolved = processing.run("native:dissolve", {
        'INPUT': final,
        'FIELD': [],
        'OUTPUT': 'memory:'
    })['OUTPUT']

    # 6. バッファ結果もFGBで保存
    buffer_out_path = os.path.join(output_dir, f"RoadBuffer_clippedby_{raster_layer.name()}.fgb")
    QgsVectorFileWriter.writeAsVectorFormat(dissolved, buffer_out_path, "UTF-8", dissolved.crs(), "FlatGeobuf")

print("全ラスターレイヤーについてクリッピング＆保存が完了しました。")
