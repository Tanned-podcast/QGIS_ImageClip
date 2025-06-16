import qgis.core
from pathlib import Path
from qgis.core import QgsFeature, QgsVectorLayer, QgsProject, QgsVectorFileWriter

#現在レイヤをnがついてない方のAllpolygonにすること
#変更箇所３つ
#出力する最初のshpファイルの通し番号を指定する
i=30
#セーブする先のshpファイルの名前決め
polygon_name=r"\no_s_"
savepath=r'C:\Users\kyohe\ishikawa_QGISimageclipPolygon\0102\SamePolygonSize_areaO\PolygonSHP_nodamage'

# レイヤAを取得
layer_a = iface.activeLayer()

#IDに応じたレイヤA内の地物を取得
target_features = layer_a.getFeatures()



for feature in target_features:
    #\を入れる文字列は必ずエスケープシークエンス無視してraw文字列にするrを使え！！！！！
    savepath2=str(Path(savepath+polygon_name+str(i)+".shp"))
    i+=1
    
    #取得した地物を新しいレイヤBとして追加
    layer = QgsVectorLayer("Polygon?crs=EPSG:4612", "Layer B", "memory")
    layer.startEditing()
    
    #addFeatureはdataProviderのもとでしか動かないことに注意
    layer.dataProvider().addFeature(feature)
    layer.commitChanges()
    
    # ファイルを書き込む　すでに同名ファイルがある場合は書き出しができないので注意
    QgsVectorFileWriter.writeAsVectorFormat(layer, savepath2, "UTF-8", layer.crs(), "GeoJson")