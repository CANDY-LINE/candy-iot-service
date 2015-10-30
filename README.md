CANDY-IoT Systemd Service
===

Intel Edison Yocto上で動作するCANDY-IoTボードを動作させるためのサービス。以下の機能を提供する。

- APN設定済みのAM Telecom社製LTE/3Gモジュールを自動起動させる

## 対応機器とファームウェア/OS
 - Intel Edison
 - Release 2.1 Yocto complete image (poky-yocto)

## インストール方法
Edisonにログインし、WiFiを起動させる。WiFiを設定していないときは、`configure-edison --wifi`にて設定すること。

```bash
Poky (Yocto Project Reference Distro) 1.7.2 binita ttyMFD2

binita login: root
Password: 
root@binita:~# ifconfig wlan0 up
```

Edisonにてインターネットにアクセスできることを確認する。
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

スクリプトをダウンロードしてインストール。
```bash
root@binita:~# curl -L https://github.com/Robotma-com/candy-iot-service/raw/master/install.sh | bash
[INFO] cdc_ether has been installed
[INFO] candy-iot service has been installed
[ALERT] *** Please reboot the system! (enter 'reboot') ***
```

上記のようにメッセージが出たら再起動する。
```bash
root@binita:~# reboot
```

再起動後、動作を確認する。

```bash
root@binita:~# systemctl status candy-iot
● candy-iot.service - CANDY-IoT Board Service
   Loaded: loaded (/lib/systemd/system/candy-iot.service; enabled)
   Active: active (exited) since Fri 2015-10-30 08:32:05 UTC; 1min 3s ago
  Process: 649 ExecStart=/opt/robotma/candy-iot/start_systemd.sh (code=exited, status=0/SUCCESS)
 Main PID: 649 (code=exited, status=0/SUCCESS)

Oct 30 08:32:04 binita start_systemd.sh[649]: root: Initializing CANDY-IoT B....
Oct 30 08:32:05 binita start_systemd.sh[649]: root: Activating LTE/3G Module...
Oct 30 08:32:05 binita start_systemd.sh[649]: udhcpc (v1.22.1) started
Oct 30 08:32:05 binita start_systemd.sh[649]: Sending discover...
Oct 30 08:32:05 binita start_systemd.sh[649]: Sending select for 192.168.225....
Oct 30 08:32:05 binita start_systemd.sh[649]: Lease of 192.168.225.22 obtain...0
Oct 30 08:32:05 binita start_systemd.sh[649]: /etc/udhcpc.d/50default: Addin...1
Oct 30 08:32:05 binita start_systemd.sh[649]: root: The interface [enp0s17u1...!
Oct 30 08:32:05 binita start_systemd.sh[649]: root: CANDY-IoT Board is initi...!
Oct 30 08:32:05 binita systemd[1]: Started CANDY-IoT Board Service.
Hint: Some lines were ellipsized, use -l to show in full.
```

## アンインストール方法
インターネットに接続し、スクリプトをダウンロードしてアンインストール。
```bash
root@binita:~# curl -L https://github.com/Robotma-com/candy-iot-service/raw/master/uninstall.sh | bash
[INFO] candy-iot has been uninstalled
[INFO] cdc_ether has been uninstalled
[ALERT] *** Please reboot the system! (enter 'reboot') ***
```

上記のようにメッセージが出たら再起動する。
```bash
root@binita:~# reboot
```

再起動後、サービスが削除されたことを確認する。

```bash
root@binita:~# systemctl status candy-iot 
● candy-iot.service
   Loaded: not-found (Reason: No such file or directory)
   Active: inactive (dead)
```

## 履歴
* 1.0.0
  - [AM Telecom社製LTE/3GモジュールAMP5200/AMP5220](http://www.amtel.co.jp/english/product/list?category=1020)に対応
