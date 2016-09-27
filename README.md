candy-iot-service
===

[![GitHub release](https://img.shields.io/github/release/CANDY-LINE/candy-iot-service.svg)](https://github.com/CANDY-LINE/candy-iot-service/releases/latest)
[![License BSD3](https://img.shields.io/github/license/CANDY-LINE/candy-iot-service.svg)](http://opensource.org/licenses/BSD-3-Clause)

candy-iot-serviceは、Intel Edison Yocto Linux上で動作する[CANDY IoTボード](http://www.candy-line.io/proandsv.html#candyiot)を動作させるためのシステムサービス（Yocto Linux上で自動的に動作するソフトウェア）です。

candy-iot-serviceや、[CANDY IoTボード](http://www.candy-line.io/proandsv.html#candyiot)に関する説明については、専用の[利用ガイド](https://github.com/CANDY-LINE/CANDY-IoT-info/blob/master/README.md)をご覧ください。

# 対応 Firmware

- [Intel® Edison Module Firmware Software Release 3.5](https://downloadmirror.intel.com/26028/eng/iot-devkit-prof-dev-image-edison-20160606.zip)
- [Release 2.1 Yocto complete image (poky-yocto)](http://downloadmirror.intel.com/25384/eng/edison-iotdk-image-280915.zip)

# 管理者向け
## モジュールリリース時の注意

1. [`install.sh`](/install.sh)内の`VERSION=`にあるバージョンを修正してコミットする
1. 履歴を追記、修正してコミットする
1. （もし必要があれば）パッケージング
```bash
$ ./install.sh pack
```

## 開発用インストール動作確認

### パッケージング

```bash
$ ./install.sh pack
(scp to Edison then ssh)
```

`edison.local`でアクセスできる場合は以下のコマンドも利用可能。
```bash
$ make
(enter Edison password)
```

### 動作確認 (Edison)

```bash
$ VERSION=2.0.0 && rm -fr tmp && mkdir tmp && cd tmp && \
  tar zxf ~/candy-iot-service-${VERSION}.tgz
$ time SRC_DIR=$(pwd) DEBUG=1 ./install.sh
$ time SRC_DIR=$(pwd) DEBUG=1 CANDY_RED=0 ./install.sh
```

# 履歴
* 2.1.0
  - Intel® Edison Module Firmware Software Release 3.5 のファームウェアに対応

* 2.0.0
  - [ltepi2-service](https://github.com/CANDY-LINE/ltepi2-service) をベースにした実装に変更
  - AM Telecom社製LTE/3GモジュールAMP520へ対応
  - CANDY REDのデフォルトフローを設定
  - CANDY IoT (late 2016) へ対応

* 1.7.0
  - コマンド名を`candy`に変更
  - CANDY REDのデフォルトフローに対応。ただし、現時点では互換性維持のためフローの内容は空としている

* 1.6.1
  - コマンド受付ソケットバックログを128に増加

* 1.6.0
  - CANDY REDをデフォルトで追加インストールする機能を追加（`CANDY_RED=0`で抑止可能）

* 1.5.0
  - AM Telecom社製LTE/3Gモジュールの自動初期設定(モデム設定とAPN設定)を追加

* 1.4.0
  - このサービスのソフトウェアバージョンを表示するコマンドを追加
  - 製品名の表記方法を変更
  - バージョン指定を一箇所に集約

* 1.3.1
  - AM Telecomモジュールモデムのウェイト時間が短いため、一部のコマンドについてモデムが応答を返す前に結果を諦めていたため、ウェイト時間を延長

* 1.3.0
  - AM TelecomモジュールへのAPN設定機能、SIM情報表示機能、モバイルネットワーク状態表示機能、モデム情報表示機能を追加
  - ドキュメントの表現を変更

* 1.2.0
  - Wi-Fi APモード動作時のLED点滅をCANDY IoTボードのLED(GPIO 14)でも点滅するように変更

* 1.1.0
  - Dockerコンテナー内で動作させるため、`KERNEL`の指定を行える機能を追加（例：`KERNEL=3.10.17-poky-edison+`）
  - インストール時のモジュールコピー先をファイルに出力できる機能を追加

* 1.0.1
  - デフォルトゲートウェイの設定が起動時に正しく行われない問題を修正

* 1.0.0
  - [AM Telecom社製LTE/3GモジュールAMP5200/AMP5220](http://www.amtel.co.jp/english/product/list?category=1020)に対応
