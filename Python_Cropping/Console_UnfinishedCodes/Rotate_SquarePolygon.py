from qgis.core import (
    QgsGeometry, QgsPointXY, QgsFeature, QgsVectorLayer,
    QgsProject, QgsCoordinateTransform, QgsWkbTypes
)
import math

sq_name = "sq_test"
sq_layer = QgsProject.instance().mapLayersByName(sq_name)[0]

def get_angle(geom):
    # 頂点リスト取得
    pts = geom.asPolygon()[0]
    # 一辺の長さ（頂点0→1間の距離）
    edge_length = math.hypot(pts[1].x() - pts[0].x(), pts[1].y() - pts[0].y())
    distance = edge_length / 2
    # QgsPointXYで線分を作成
    line = QgsGeometry.fromPolylineXY([QgsPointXY(pts[0]), QgsPointXY(pts[1])])
    return line.interpolateAngle(distance)

def align_polygons_by_angle(layer):
    # 1. フィーチャ取得（2つと仮定）
    features = list(layer.getFeatures())
    if len(features) < 2:
        raise ValueError("2つ以上のポリゴンが必要です")
    featA, featB = features[0], features[1]
    geomA = featA.geometry()
    geomB = featB.geometry()

    # 2. 各ポリゴンの頂点0→1の角度を取得
    angleA = get_angle(geomA)
    angleB = get_angle(geomB)
    print(f"angleA: {angleA*180/math.pi:.2f}°, angleB: {angleB*180/math.pi:.2f}°")

    # 3. 角度差分
    diff_angle = (angleB - angleA) % (2*math.pi)
    diff_angle_deg = diff_angle * 180 / math.pi
    print(f"角度差分: {diff_angle_deg:.2f}°")

    # 4. 角度差分に応じた頂点ペアの辞書（例：必要に応じて変更可）
    #角度差分を45度で割った余りの階級と，ポリゴンAの頂点番号，ポリゴンBの頂点番号
    vertex_pair_dict = {
        0: (2, 3),
        1: (0, 0),
        2: (1, 3),
        3: (3, 0),
        4: (0, 3),
        5: (2, 0),
        6: (3, 3),
        7: (1, 0),
    }
    # どの階級かを決定
    bin_idx = int(diff_angle_deg // 45) % 8
    idxA, idxB = vertex_pair_dict[bin_idx]
    print(f"対応する辞書ID:{bin_idx}, 対応する頂点ペア: idxA={idxA}, idxB={idxB}")

    ptsA = geomA.asPolygon()[0]
    ptsB = geomB.asPolygon()[0]

    # 5. 平行移動ベクトル計算
    vec_x = ptsA[idxA].x() - ptsB[idxB].x()
    vec_y = ptsA[idxA].y() - ptsB[idxB].y()

    # 6. ポリゴンBに平行移動を適用
    geomB.translate(vec_x, vec_y)
    print(f"頂点同士を対応、ベクトル({vec_x:.3f},{vec_y:.3f}) 移動しました。")

    # レイヤの編集モードでジオメトリを更新
    layer.startEditing()
    layer.changeGeometry(featB.id(), geomB)
    layer.commitChanges()

    return geomB

# 実行例
align_polygons_by_angle(sq_layer)
