from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject

#道路ネットワーク非表示
#事前にそのエリアの空撮画像全部マージして1枚にしておくこと
#変更箇所6つ　ラスタレイヤ名と始点と終点ポリゴン番号とsavepathとポリゴン名
#ポリゴン名は必ずアルファベットと数字の間に_入れる

#始点と終点のポリゴンの番号を指定
id_start=0
id_end=38

Allarea_name="areaR_all"
rpolygon_name=r"\r"
polygon_name="r_"

savepath=r'C:\Users\kyohe\ishikawa_QGISimageclipPolygon\0102\areaR\ClippedPNG'

# ラスターレイヤの読み込み
raster_layer = QgsProject.instance().mapLayersByName(Allarea_name)[0]

print("raster layer:", raster_layer)

for i in range(id_start, id_end+1):
    savepath2=str(Path(savepath+rpolygon_name+str(i)+".png"))
    layername=polygon_name+str(i)
    
    # ポリゴンのレイヤの読み込み
    polygon_layer = QgsProject.instance().mapLayersByName(layername)[0]
    
    # クリップ処理の実行
    params = {
    'INPUT': raster_layer,
    'OUTPUT': savepath2,
    'MASK': polygon_layer,
    }
    processing.run('gdal:cliprasterbymasklayer', params)