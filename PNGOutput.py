from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject

# ラスターレイヤの読み込み
raster_layer = QgsProject.instance().mapLayersByName('a1_modified')[0]

print("raster layer:", raster_layer)

#始点と終点のポリゴンの番号を指定
id_start=4
id_end=12

savepath=r'C:\Users\kyohe\ishikawa_QGISimageclipPolygon\0105\a1'

for i in range(id_start, id_end+1):
    savepath2=str(Path(savepath+r"\a1_"+str(i)+".png"))
    layername='a1_'+str(i)
    
    # ポリゴンのレイヤの読み込み
    polygon_layer = QgsProject.instance().mapLayersByName(layername)[0]
    
    # クリップ処理の実行
    params = {
    'INPUT': raster_layer,
    'OUTPUT': savepath2,
    'MASK': polygon_layer,
    }
    processing.run('gdal:cliprasterbymasklayer', params)