#道路端レイヤーの色を一括で変えて見やすくする
import qgis.core
from qgis.PyQt.QtGui import QColor

# 選択中のレイヤーを取得
for layer in iface.layerTreeView().selectedLayers():
    if layer.type() == layer.VectorLayer:
        renderer = layer.renderer()
        symbol = renderer.symbol()
        # 色を赤に設定
        symbol.setColor(QColor(183, 63, 149))
        # 透明度を50%に設定
        symbol.setOpacity(0.5)
        # レイヤーをリフレッシュ
        layer.triggerRepaint()
