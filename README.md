CANDY IoT Board Service
===

本サービスは、Intel Edison Yocto上で動作するCANDY IoTボードを動作させるためのサービスです。

![CANDY IoT Image(1)](images/CANDY IoT-1.jpg "CANDY IoT Image 1")


![CANDY IoT Image(2)](images/CANDY IoT-2.jpg "CANDY IoT Image 2")

このサービスでは、以下の機能を提供しています。

- AM Telecom社製LTE/3Gモジュールの自動起動
- AM Telecom社製LTE/3Gモジュールを操作するコマンドラインツール
  - APN設定、表示
  - LTE/3Gネットワーク状態表示
  - SIM状態表示
  - モデム情報表示
- Wi-Fi APモード起動時にCANDY IoTボード上でLEDを点滅

## 対応機器とファームウェア/OS
 - Intel Edison
 - Release 2.1 Yocto complete image (poky-yocto)

## インストール方法
**インストールには、インターネットに接続できるWi-Fiのアクセスポイントが必要です。**

まず最初にEdisonにログインします。続いて、WiFiを起動させてください。もしWiFiを設定していないときは、`configure-edison --wifi`にて、Wi−Fiの設定を行ってください。

```bash
Poky (Yocto Project Reference Distro) 1.7.2 binita ttyMFD2

binita login: root
Password: 
root@binita:~# ifconfig wlan0 up
```

Wi-Fi起動後、Edisonにてインターネットにアクセスできることを確認してください。
以下のようなcURLコマンドを実行して結果を得られれば問題ありません。

```bash
root@binita:~# curl -i -L -X HEAD http://www.robotma.com/
HTTP/1.1 200 OK
Date: Fri, 30 Oct 2015 04:43:43 GMT
Server: Apache
Last-Modified: Mon, 14 Sep 2015 07:08:39 GMT
ETag: "41ed5a-1947-bc184bc0"
Accept-Ranges: bytes
Content-Length: 6471
Content-Type: text/html

curl: (18) transfer closed with 6471 bytes remaining to read
root@binita:~# 
```

GitHub上にあるスクリプトをダウンロードしてインストールします。

```bash
root@binita:~# curl -L \
  https://github.com/Robotma-com/candy-iot-service/raw/master/install.sh \
  | bash
[INFO] cdc_ether has been installed
ln -s '/lib/systemd/system/candy-iot.service' '/etc/systemd/system/multi-user.target.wants/candy-iot.service'
[INFO] candy-iot service has been installed
[ALERT] *** Please reboot the system! (enter 'reboot') ***
```

インストール完了後、上記のようにメッセージが出ますので、以下のコマンドにて再起動させてください。

```bash
root@binita:~# reboot
```

再起動後、動作状況を確認します。

```bash
root@binita:~# systemctl status candy-iot
● candy-iot.service - CANDY IoT Board Service
   Loaded: loaded (/lib/systemd/system/candy-iot.service; enabled)
   Active: active (exited) since Fri 2015-10-30 09:20:31 UTC; 32s ago
  Process: 268 ExecStart=/opt/robotma/candy-iot/start_systemd.sh (code=exited, status=0/SUCCESS)
 Main PID: 268 (code=exited, status=0/SUCCESS)
   CGroup: /system.slice/candy-iot.service
           └─374 udhcpc -i enp0s17u1

Oct 30 09:20:28 binita start_systemd.sh[268]: udhcpc (v1.22.1) started
Oct 30 09:20:28 binita start_systemd.sh[268]: Sending discover...
Oct 30 09:20:31 binita start_systemd.sh[268]: Sending select for 192.168.225....
Oct 30 09:20:31 binita start_systemd.sh[268]: Lease of 192.168.225.37 obtain...0
Oct 30 09:20:31 binita start_systemd.sh[268]: /etc/udhcpc.d/50default: Addin...1
Oct 30 09:20:31 binita start_systemd.sh[268]: root: The interface [enp0s17u1...!
Oct 30 09:20:31 binita root[375]: The interface [enp0s17u1] is up!
Oct 30 09:20:31 binita start_systemd.sh[268]: root: CANDY IoT Board is initi...!
Oct 30 09:20:31 binita root[376]: CANDY IoT Board is initialized successfully!
Oct 30 09:20:31 binita systemd[1]: Started CANDY IoT Board Service.
Hint: Some lines were ellipsized, use -l to show in full.
```

なお上記の`enp0s17u1`が、LTE/3Gモジュールのネットワークインタフェースとなります。

```bash
root@binita:~# ifconfig enp0s17u1
enp0s17u1 Link encap:Ethernet  HWaddr 99:99:99:99:99:99  
          inet addr:192.168.225.37  Bcast:192.168.225.255  Mask:255.255.255.0
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:6 errors:0 dropped:0 overruns:0 frame:0
          TX packets:30 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000 
          RX bytes:768 (768.0 B)  TX bytes:4234 (4.1 KiB)
```

## アンインストール方法
アンインストールを行うためには、専用のスクリプトを実行します。このスクリプトは動作中のサービスを停止し、関連ファイルをすべて削除します。

まず`/opt/robotma/candy-iot/uninstall.sh`を実行します。

```bash
root@binita:~# /opt/robotma/candy-iot/uninstall.sh
[INFO] candy-iot has been uninstalled
[INFO] cdc_ether has been uninstalled
[ALERT] *** Please reboot the system! (enter 'reboot') ***
```

上記のようにメッセージが出たら再起動してください。

```bash
root@binita:~# reboot
```

再起動後、サービスが削除されたことを確認します。

```bash
root@binita:~# systemctl status candy-iot 
● candy-iot.service
   Loaded: not-found (Reason: No such file or directory)
   Active: inactive (dead)
```

削除後は、LTE/3Gモジュールのネットワークインタフェースも見えなくなります。

```bash
root@binita:~# ifconfig enp0s17u1
enp0s17u1: error fetching interface information: Device not found
```

## コマンドラインツール使用方法
LTE/3Gモジュールの情報を取得したり、設定したりするため、`ciot`というコマンドを利用します。
このコマンドは、`/usr/bin`にインストールされるため、インストール完了後（再起動後）にすぐ利用することができます。

### APNの表示
現在設定されているAPNを表示します。パスワードは表示されません。

```bash
root@edison:~# ciot apn ls
{
  "apns": [
    {
      "apn": "iijmio.jp", 
      "user": "iij"
    }
  ]
}
```

### APNの設定
APNを設定します。単一のAPNのみ設定することができます。

```bash
root@edison:~# ciot apn set -n APN名 -u ユーザーID -p パスワード
```

### ネットワーク状態の表示
モバイルネットワークの状態を表示します。Wi-Fiの状態ではありません。
rssiの単位は`dBm`となります。結果文字列の`rssiDesc`には以下の値が入ります。

1. `"OR_LESS"` ... **`rssi`の値以下**であることを示す
1. `"OR_MORE"` ... **`rssi`の値以上**であることを示す
1. `"NO_SIGANL"` ... 圏外
1. `""` ... `rssi`の数値通り

`network`のプロパティは、`ONLINE`、`OFFLINE`または`UNKNOWN`が入ります。

```bash
root@edison:~# ciot network show
{
  "rssi": "-85", 
  "network": "ONLINE", 
  "rssiDesc": ""
}
```

### SIM状態の表示
SIMの状態を表示します。
結果文字列の`state`には、以下の文字列が入ります。

1. `SIM_STATE_READY` ... SIMが認識されている
1. `SIM_STATE_ABSENT` ... SIMが認識されていない

```bash
root@edison:~# ciot sim show
{
  "msisdn": "11111111111", 
  "state": "SIM_STATE_READY", 
  "imsi": "440111111111111"
}
```

### モデム状態の表示
モデム状態を表示します。

```bash
root@edison:~# ciot modem show
{
  "imei": "999999999999999", 
  "model": "AMP5200", 
  "manufacturer": "AM Telecom", 
  "revision": "14-01"
}
```

## モジュールリリース時の注意

1. [`install.sh`](/install.sh)内の`VERSION=`にあるバージョンを修正してコミットする
1. [`candy-iot.service`](/systemd/candy-iot.service)内の`Description`にあるバージョンを修正してコミットする
1. 履歴を追記、修正してコミットする

## 履歴
* 1.3.1
  - AM Telecomモジュールモデムのウェイト時間が短いため、一部のコマンドについてモデムが応答を返す前に結果を諦めていたため、ウェイト時間を延長

* 1.3.0
  - AM TelecomモジュールへのAPN設定機能、SIM情報表示機能、モバイルネットワーク状態表示機能、モデム情報表示機能を追加
  - ドキュメントの表現を変更

* 1.2.0
  - WiFi APモード動作時のLED点滅をCANDY IoTボードのLED(GPIO 14)でも点滅するように変更

* 1.1.0
  - Dockerコンテナー内で動作させるため、`KERNEL`の指定を行える機能を追加（例：`KERNEL=3.10.17-poky-edison+`）
  - インストール時のモジュールコピー先をファイルに出力できる機能を追加

* 1.0.1
  - デフォルトゲートウェイの設定が起動時に正しく行われない問題を修正

* 1.0.0
  - [AM Telecom社製LTE/3GモジュールAMP5200/AMP5220](http://www.amtel.co.jp/english/product/list?category=1020)に対応
