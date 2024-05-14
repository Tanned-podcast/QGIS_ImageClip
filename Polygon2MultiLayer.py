import qgis.core
from pathlib import Path
from qgis.core import QgsFeature, QgsVectorLayer, QgsProject, QgsVectorFileWriter

savepath=r'C:\Users\kyohe\ishikawa_QGISimageclipPolygon\0105\a1'

# レイヤAを取得
layer_a = iface.activeLayer()

#IDに応じたレイヤA内の地物を取得
target_features = layer_a.getFeatures()

#出力する最初のフshpファイルの通し番号を指定する
i=0

for feature in target_features:
    #\を入れる文字列は必ずエスケープシークエンス無視してraw文字列にするrを使え！！！！！
    savepath2=str(Path(savepath+r"\a1_"+str(i)+".shp"))
    i+=1
    
    #取得した地物を新しいレイヤBとして追加
    layer = QgsVectorLayer("Polygon?crs=EPSG:4612", "Layer B", "memory")
    layer.startEditing()
    
    #addFeatureはdataProviderのもとでしか動かないことに注意
    layer.dataProvider().addFeature(feature)
    layer.commitChanges()
    
    # ファイルを書き込む　すでに同名ファイルがある場合は書き出しができないので注意
    QgsVectorFileWriter.writeAsVectorFormat(layer, savepath2, "UTF-8", layer.crs(), "GeoJson")

