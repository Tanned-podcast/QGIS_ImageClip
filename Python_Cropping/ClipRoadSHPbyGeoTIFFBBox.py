from qgis.core import QgsProject, QgsRasterLayer, QgsVectorLayer
import processing

rasterlayer_name="a2"
vectorlayer_name="hokuriku_road_buffer"

# 対象のラスターレイヤー名またはオブジェクト
raster_layer = QgsProject.instance().mapLayersByName(rasterlayer_name)[0]

# ラスター自体の表示範囲（extent）を取得
extent = raster_layer.extent()
xmin = extent.xMinimum()
xmax = extent.xMaximum()
ymin = extent.yMinimum()
ymax = extent.yMaximum()

# extent を "xmin,xmax,ymin,ymax" の文字列に整形（CRS オプション付き）
crs = raster_layer.crs().authid()  # 例： "EPSG:4326"
ext_str = f"{xmin},{xmax},{ymin},{ymax} [{crs}]"

# 対象のベクターレイヤー
vector_layer = QgsProject.instance().mapLayersByName(vectorlayer_name)[0]

# Extract by extent ツールを利用して切り取り
params = {
    'INPUT': vector_layer,
    'EXTENT': ext_str,
    'CLIP': True,            # ポリゴン形状で切り取る
    'OUTPUT': 'memory:'      # 一時レイヤーとして出力
}
res = processing.run("qgis:extractbyextent", params)
clipped_layer = res['OUTPUT']

# 結果を現在の QGIS プロジェクトへ追加
QgsProject.instance().addMapLayer(clipped_layer)
