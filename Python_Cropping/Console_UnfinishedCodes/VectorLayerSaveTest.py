import os
import sys

# QGISの環境設定
qgis_path = r"C:\Program Files\QGIS 3.36.2"
#qgis.coreに繋ぐパス
sys.path.append(r"C:\Program Files\QGIS 3.36.2\apps\qgis\python")
sys.path.append(r"C:\Program Files\QGIS 3.36.2\apps\qgis\python\plugins")

from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsField
)
from PyQt5.QtCore import QVariant
import xml.etree.ElementTree as ET
import math
from typing import List, Tuple, Dict


output_path = r"C:\Users\kyohe\ishikawa_QGISimageclipPolygon\misc\CenterlinefromEdge.fgb"

centerline_features = []

# フィーチャを作成

# 中心線のジオメトリを作成
center_points = []

points1 = QgsPointXY(136.7302309, 37.1218538)
points2 = QgsPointXY(136.7314150, 37.1218780)

center_points.append(points1)
center_points.append(points2)


centerline_geom = QgsGeometry.fromPolylineXY(center_points)

feature = QgsFeature()
feature.setGeometry(centerline_geom)

centerline_features.append(feature)

def save_centerlines(features, output_path: str) -> bool:
        """
        生成した中心線をFGBファイルに保存（QGIS 3.36.2対応）
        """
        try:
            # 中心線レイヤーを作成
            centerline_layer = QgsVectorLayer("LineString?crs=EPSG:6668", "Road_Centerlines", "memory")

            # フィールドを追加
            provider = centerline_layer.dataProvider()
            provider.addAttributes([
                QgsField("id", QVariant.Int),
                QgsField("length", QVariant.Double)
            ])
            centerline_layer.updateFields()

            # フィーチャを追加
            provider.addFeatures(features)

            # 新しい推奨APIでFGB形式で保存
            from qgis.core import QgsVectorFileWriter, QgsProject
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "FlatGeobuf"
            options.fileEncoding = "UTF-8"
            errorcode, error, _, _ = QgsVectorFileWriter.writeAsVectorFormatV3(
                centerline_layer,
                output_path,
                QgsProject.instance().transformContext(),
                options
            )

            if errorcode == QgsVectorFileWriter.NoError:
                print(f"中心線を {output_path} に保存しました")
                return True
            else:
                print(f"中心線保存エラー: {error}")
                return False

        except Exception as e:
            print(f"中心線保存エラー: {e}")
            return False
        
save_centerlines(centerline_features, output_path)