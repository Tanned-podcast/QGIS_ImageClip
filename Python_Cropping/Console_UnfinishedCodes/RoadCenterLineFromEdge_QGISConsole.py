"""
QGIS Pythonコンソール用 道路中心線生成スクリプト
Road Centerline Generation Script for QGIS Python Console

使用方法：
1. QGISのPythonコンソールを開く
2. このスクリプトをコピー&ペーストして実行
3. または、スクリプトファイルを読み込んで実行

注意：このスクリプトはQGIS環境内で実行することを前提としています
"""

import os
import sys
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsProject,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsField,
    QgsProcessingFeedback, QgsProcessingUtils
)
from qgis.PyQt.QtCore import QVariant
import xml.etree.ElementTree as ET
import math
from typing import List, Tuple, Dict

xml_file_path = r"C:\Users\kyohe\石川県基盤地図情報\道路縁\Road_Edge\FG-GML-553656-RdEdg-20230701-0001.xml"


def load_xml_road_edges_qgis(xml_file_path: str) -> List[QgsFeature]:
    """
    XMLファイルから道路縁データを読み込み（GML名前空間・gml:posList対応）
    """
    edge_features = []
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        ns = {
            'gml': 'http://www.opengis.net/gml/3.2',
            'fgd': 'http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema'
        }
        # <RdEdg>タグをすべて取得
        for edge_elem in root.findall('.//fgd:RdEdg', ns):
            coordinates = []
            # <gml:posList>をすべて取得
            for poslist_elem in edge_elem.findall('.//gml:posList', ns):
                pos_text = poslist_elem.text.strip()
                pos_values = [float(v) for v in pos_text.split()]
                # 2つずつ取り出して座標にする（緯度 経度の順）
                for i in range(0, len(pos_values), 2):
                    lat = pos_values[i]
                    lon = pos_values[i+1]
                    coordinates.append(QgsPointXY(lon, lat))  # QGISは(x, y)=(経度, 緯度)
            if len(coordinates) >= 2:
                line_geom = QgsGeometry.fromPolylineXY(coordinates)
                feature = QgsFeature()
                feature.setGeometry(line_geom)
                edge_features.append(feature)
        print(f"道路縁データを {len(edge_features)} 件読み込みました")
        return edge_features
    except Exception as e:
        print(f"XMLファイルの読み込みエラー: {e}")
        return []


def find_parallel_edges_qgis(edge_features: List[QgsFeature], tolerance: float = 10.0) -> List[Tuple[QgsFeature, QgsFeature]]:
    """
    並行する道路縁のペアを特定（QGIS環境用）
    
    Args:
        edge_features: 道路縁フィーチャのリスト
        tolerance: 並行判定の許容距離（メートル）
        
    Returns:
        List[Tuple]: 並行する道路縁のペアのリスト
    """
    parallel_pairs = []
    
    for i, edge1 in enumerate(edge_features):
        for j, edge2 in enumerate(edge_features[i+1:], i+1):
            if are_parallel_edges_qgis(edge1, edge2, tolerance):
                parallel_pairs.append((edge1, edge2))
    
    print(f"並行する道路縁のペアを {len(parallel_pairs)} 組見つけました")
    return parallel_pairs


def are_parallel_edges_qgis(edge1: QgsFeature, edge2: QgsFeature, tolerance: float) -> bool:
    """
    2つの道路縁が並行しているか判定（QGIS環境用）
    
    Args:
        edge1: 道路縁1
        edge2: 道路縁2
        tolerance: 許容距離
        
    Returns:
        bool: 並行している場合True
    """
    geom1 = edge1.geometry()
    geom2 = edge2.geometry()
    
    if not geom1 or not geom2:
        return False
    
    # 2つのラインの距離を計算
    distance = geom1.distance(geom2)
    
    # 距離が許容範囲内で、かつ方向が類似している場合に並行と判定
    if distance <= tolerance:
        return check_direction_similarity_qgis(geom1, geom2)
    
    return False


def check_direction_similarity_qgis(geom1: QgsGeometry, geom2: QgsGeometry) -> bool:
    """
    2つのラインの方向の類似性をチェック（QGIS環境用）
    
    Args:
        geom1: ジオメトリ1
        geom2: ジオメトリ2
        
    Returns:
        bool: 方向が類似している場合True
    """
    try:
        # ラインの開始点と終了点を取得
        points1 = geom1.asPolyline()
        points2 = geom2.asPolyline()
        
        if len(points1) < 2 or len(points2) < 2:
            return False
        
        # 方向ベクトルを計算
        dir1 = QgsPointXY(points1[-1].x() - points1[0].x(), 
                         points1[-1].y() - points1[0].y())
        dir2 = QgsPointXY(points2[-1].x() - points2[0].x(), 
                         points2[-1].y() - points2[0].y())
        
        # 角度を計算
        angle1 = math.atan2(dir1.y(), dir1.x())
        angle2 = math.atan2(dir2.y(), dir2.x())
        
        # 角度差を計算（絶対値）
        angle_diff = abs(angle1 - angle2)
        angle_diff = min(angle_diff, 2 * math.pi - angle_diff)
        
        # 30度以内の角度差を類似と判定
        return angle_diff <= math.radians(30)
        
    except Exception:
        return False


def generate_centerlines_qgis(parallel_pairs: List[Tuple[QgsFeature, QgsFeature]]) -> List[QgsFeature]:
    """
    並行する道路縁のペアから中心線を生成（QGIS環境用）
    
    Args:
        parallel_pairs: 並行する道路縁のペアのリスト
        
    Returns:
        List[QgsFeature]: 中心線フィーチャのリスト
    """
    centerline_features = []
    
    for edge1, edge2 in parallel_pairs:
        centerline = calculate_centerline_qgis(edge1, edge2)
        if centerline:
            centerline_features.append(centerline)
    
    print(f"中心線を {len(centerline_features)} 本生成しました")
    return centerline_features


def calculate_centerline_qgis(edge1: QgsFeature, edge2: QgsFeature) -> QgsFeature:
    """
    2つの道路縁から中心線を計算（QGIS環境用）
    
    Args:
        edge1: 道路縁1
        edge2: 道路縁2
        
    Returns:
        QgsFeature: 中心線のフィーチャ
    """
    try:
        geom1 = edge1.geometry()
        geom2 = edge2.geometry()
        
        if not geom1 or not geom2:
            return None
        
        # 各ラインの点を取得
        points1 = geom1.asPolyline()
        points2 = geom2.asPolyline()
        
        # 中心線の点を計算
        center_points = []
        
        # 短い方のラインに合わせて中心点を計算
        min_length = min(len(points1), len(points2))
        
        for i in range(min_length):
            # 対応する点の中心を計算
            center_x = (points1[i].x() + points2[i].x()) / 2
            center_y = (points1[i].y() + points2[i].y()) / 2
            center_points.append(QgsPointXY(center_x, center_y))
        
        # 中心線のジオメトリを作成
        centerline_geom = QgsGeometry.fromPolylineXY(center_points)
        
        # フィーチャを作成
        feature = QgsFeature()
        feature.setGeometry(centerline_geom)
        
        return feature
        
    except Exception as e:
        print(f"中心線計算エラー: {e}")
        return None


def save_centerlines_to_layer_qgis(centerline_features: List[QgsFeature], layer_name: str = "Road_Centerlines") -> QgsVectorLayer:
    """
    生成した中心線をQGISレイヤーとして保存（QGIS環境用）
    
    Args:
        centerline_features: 中心線フィーチャのリスト
        layer_name: レイヤー名
        
    Returns:
        QgsVectorLayer: 作成されたレイヤー
    """
    try:
        # 中心線レイヤーを作成
        centerline_layer = QgsVectorLayer("LineString?crs=EPSG:6668", layer_name, "memory")
        
        # フィールドを追加
        provider = centerline_layer.dataProvider()
        provider.addAttributes([
            QgsField("id", QVariant.Int),
            QgsField("length", QVariant.Double)
        ])
        centerline_layer.updateFields()
        
        # フィーチャを追加
        if centerline_features:
            provider.addFeatures(centerline_features)
        
        # レイヤーをプロジェクトに追加
        QgsProject.instance().addMapLayer(centerline_layer)
        
        print(f"中心線レイヤー '{layer_name}' をプロジェクトに追加しました")
        return centerline_layer
        
    except Exception as e:
        print(f"中心線レイヤー作成エラー: {e}")
        return None


def generate_road_centerlines_from_xml(xml_file_path: str, tolerance: float = 10.0):
    """
    XMLファイルから道路中心線を生成し、QGISプロジェクトにスクラッチレイヤとして追加する
    """
    print("=== 道路中心線生成処理開始 ===")
    edge_features = load_xml_road_edges_qgis(xml_file_path)
    if not edge_features:
        print("道路縁データの読み込みに失敗しました。")
        return
    parallel_pairs = find_parallel_edges_qgis(edge_features, tolerance)
    if not parallel_pairs:
        print("並行する道路縁のペアが見つかりませんでした。")
        return
    centerline_features = generate_centerlines_qgis(parallel_pairs)
    if not centerline_features:
        print("中心線の生成に失敗しました。")
        return
    # QGISレイヤーとして追加（ファイル保存はしない）
    layer = save_centerlines_to_layer_qgis(centerline_features)
    print("=== 道路中心線生成処理完了 ===")

generate_road_centerlines_from_xml(xml_file_path, 10.0)