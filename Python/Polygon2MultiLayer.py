import qgis.core
from pathlib import Path
from qgis.core import QgsFeature, QgsVectorLayer, QgsProject, QgsVectorFileWriter

#現在レイヤをnがついてない方のAllpolygonにすること
#変更箇所３つ
#出力する最初のshpファイルの通し番号を指定する
i=0
#セーブする先のshpファイルの名前決め
polygon_name=r"\a13_rotated_test_"
savepath=r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\misc\SqAlign_MultiWidth_a13_Test"

#複数ポリゴンが入ってて分けたいレイヤの名前
vectorlayer_name="sq_test"
vectorlayer = QgsProject.instance().mapLayersByName(vectorlayer_name)[0]

#IDに応じたレイヤA内の地物を取得
target_features = vectorlayer.getFeatures()



for feature in target_features:
    #\を入れる文字列は必ずエスケープシークエンス無視してraw文字列にするrを使え！！！！！
    savepath2=str(Path(savepath+polygon_name+str(i)+".fgb"))
    i+=1
    
    #取得した地物を新しいレイヤBとして追加
    layer = QgsVectorLayer("Polygon?crs=EPSG:4612", "Layer B", "memory")
    layer.startEditing()
    
    #addFeatureはdataProviderのもとでしか動かないことに注意
    layer.dataProvider().addFeature(feature)
    layer.commitChanges()
    
    # ファイルを書き込む　すでに同名ファイルがある場合は書き出しができないので注意
    QgsVectorFileWriter.writeAsVectorFormat(layer, savepath2, "UTF-8", layer.crs(), "GeoJson")

