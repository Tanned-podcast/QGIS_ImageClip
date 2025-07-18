# 道路中心線生成スクリプト

## 概要

このスクリプトは、QGISにおいて道路縁のXMLデータから道路中心線を自動生成するためのPythonスクリプトです。

## ファイル構成

- `RoadCenterLineFromEdge.py` - スタンドアロン版のスクリプト
- `RoadCenterLineFromEdge_QGISConsole.py` - QGISコンソール用のスクリプト
- `README_RoadCenterline.md` - このファイル

## 機能

1. **XMLファイル読み込み**: 道路縁の座標データをXMLファイルから読み込み
2. **並行道路縁の特定**: 距離と方向の類似性に基づいて並行する道路縁のペアを特定
3. **中心線計算**: 並行する道路縁のペアから中心線を計算
4. **結果保存**: 生成された中心線をQGISレイヤーまたはファイルとして保存

## 使用方法

### 方法1: QGISコンソールでの実行

1. QGISを起動
2. メニューから「プラグイン」→「Pythonコンソール」を開く
3. 以下のコードを実行：

```python
# スクリプトファイルを読み込み
exec(open('path/to/RoadCenterLineFromEdge_QGISConsole.py').read())

# 道路中心線を生成
generate_road_centerlines_from_xml(
    xml_file_path="path/to/road_edges.xml",
    output_path="path/to/output.shp",  # 省略可能
    tolerance=10.0  # 並行判定の許容距離（メートル）
)
```

### 方法2: スタンドアロン実行

```bash
python RoadCenterLineFromEdge.py
```

実行時に以下の情報を入力：
- 道路縁のXMLファイルのパス
- 出力ファイルのパス（.shp形式）

## XMLファイル形式

スクリプトは以下のXML構造に対応しています：

### 形式1: 属性ベース
```xml
<road_edges>
    <road_edge>
        <coordinate x="139.7670" y="35.6812"/>
        <coordinate x="139.7671" y="35.6813"/>
        <!-- 追加の座標点 -->
    </road_edge>
    <!-- 追加の道路縁 -->
</road_edges>
```

### 形式2: テキストベース
```xml
<road_edges>
    <road_edge>
        <coordinate>139.7670,35.6812</coordinate>
        <coordinate>139.7671,35.6813</coordinate>
        <!-- 追加の座標点 -->
    </road_edge>
    <!-- 追加の道路縁 -->
</road_edges>
```

### 形式3: 経緯度形式
```xml
<road_edges>
    <road_edge>
        <coordinate lon="139.7670" lat="35.6812"/>
        <coordinate lon="139.7671" lat="35.6813"/>
        <!-- 追加の座標点 -->
    </road_edge>
    <!-- 追加の道路縁 -->
</road_edges>
```

## パラメータ

### tolerance（許容距離）
- 並行する道路縁を判定する際の距離の閾値
- 単位：メートル
- デフォルト：10.0
- 道路幅に応じて調整してください

### 座標系
- デフォルト：EPSG:6668（JGD2011 / Japan Plane Rectangular CS）
- 必要に応じてスクリプト内で変更してください

## 出力

### QGISレイヤー
- メモリレイヤーとして「Road_Centerlines」が作成されます
- 自動的にプロジェクトに追加されます

### ファイル出力
- ESRI Shapefile形式（.shp）
- フィールド：
  - `id`: 中心線のID
  - `length`: 中心線の長さ

## 注意事項

1. **座標系の確認**: 入力XMLファイルの座標系とQGISプロジェクトの座標系が一致していることを確認してください
2. **データ品質**: 道路縁データの品質が中心線の精度に影響します
3. **メモリ使用量**: 大量の道路縁データを処理する場合は、メモリ使用量に注意してください
4. **並行判定**: 複雑な道路形状では、並行判定が正しく動作しない場合があります

## トラブルシューティング

### よくある問題

1. **XMLファイルが読み込めない**
   - ファイルパスが正しいか確認
   - XMLファイルの形式が対応しているか確認

2. **並行する道路縁が見つからない**
   - `tolerance`パラメータを調整
   - 道路縁データの品質を確認

3. **中心線が正しく生成されない**
   - 道路縁のペアが正しく特定されているか確認
   - 座標系の設定を確認

### デバッグ情報

スクリプト実行時に以下の情報が出力されます：
- 読み込まれた道路縁データの数
- 特定された並行ペアの数
- 生成された中心線の数
- エラーメッセージ（発生時）

## カスタマイズ

### XMLタグの変更
スクリプト内の以下の部分を変更して、異なるXMLタグに対応できます：

```python
edge_elements = root.findall('.//road_edge') or root.findall('.//edge') or root.findall('.//line')
```

### 並行判定の調整
`check_direction_similarity_qgis`関数内の角度閾値を変更できます：

```python
# 30度以内の角度差を類似と判定
return angle_diff <= math.radians(30)  # この値を調整
```

## ライセンス

このスクリプトは教育・研究目的で自由に使用できます。

## 更新履歴

- v1.0: 初回リリース
  - 基本的な道路中心線生成機能
  - QGISコンソール対応
  - 複数のXML形式対応 