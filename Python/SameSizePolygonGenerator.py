from qgis.core import QgsProject, QgsGeometry, QgsPointXY, QgsFeature, QgsVectorLayer, QgsWkbTypes
#既存の大きさが違うポリゴンだらけのレイヤから全てのポリゴンの大きさが等しいレイヤを作るプログラム
#既存のレイヤで置いたポリゴンの中心位置を引き継ぐ
#変更箇所3か所：既存レイヤ名と新規レイヤ名とポリゴン長さ

original_layer_name = "NO_big"
target_layer_name = "AllPolygon_NO_SameSize"

#特定の長さ
target_length = 0.001
half_length=target_length/2

#既存レイヤを取得
original_layer = QgsProject.instance().mapLayersByName(original_layer_name)[0]

#新規レイヤーを作成
target_layer = QgsVectorLayer("Polygon?crs=EPSG:4612", target_layer_name, "memory")
target_layer.startEditing()

#最初のポリゴンの中心を取得して新しいポリゴンを生成
for feature in original_layer.getFeatures():
    geom = feature.geometry()
    if geom.type() == QgsWkbTypes.PolygonGeometry:
        centroid = geom.centroid().asPoint()
        points = [
            QgsPointXY(centroid.x() - half_length, centroid.y() - half_length),
            QgsPointXY(centroid.x() + half_length, centroid.y() - half_length),
            QgsPointXY(centroid.x() + half_length, centroid.y() + half_length),
            QgsPointXY(centroid.x() - half_length, centroid.y() + half_length),
            QgsPointXY(centroid.x() - half_length, centroid.y() - half_length)
        ]
        geom = QgsGeometry.fromPolygonXY([points])
        
        # 正方形のフィーチャを作成
        target_feature = QgsFeature()
        target_feature.setGeometry(geom)
        target_layer.addFeature(target_feature)
        
        

#編集をコミット コミットは最後に一気にやるもの
target_layer.commitChanges()


# プロジェクトにレイヤーを追加
QgsProject.instance().addMapLayer(target_layer)