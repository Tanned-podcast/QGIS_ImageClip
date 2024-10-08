from qgis.core import QgsRasterLayer, QgsVectorLayer, QgsProject

# ラスターレイヤの読み込み
raster_layer = QgsProject.instance().mapLayersByName('areaF_all')[0]

print("raster layer:", raster_layer)

#始点と終点のポリゴンの番号を指定
id_start=0
id_end=7

savepath=r'C:\Users\kyohe\ishikawa_QGISimageclipPolygon\0117\areaF\ClippedPNG_nodamage'

for i in range(id_start, id_end+1):
    savepath2=str(Path(savepath+r"\nf_"+str(i)+".png"))
    layername='nf_'+str(i)
    
    # ポリゴンのレイヤの読み込み
    polygon_layer = QgsProject.instance().mapLayersByName(layername)[0]
    
    # クリップ処理の実行
    params = {
    'INPUT': raster_layer,
    'OUTPUT': savepath2,
    'MASK': polygon_layer,
    }
    processing.run('gdal:cliprasterbymasklayer', params)