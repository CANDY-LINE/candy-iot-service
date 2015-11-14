
class SerialPortEmurator:
  def __init__(self):
    self.res = {
      'AT+CGDCONT?': [
        "(ECHO_BACK)",
        "",
        "",
        "+CGDCONT: 1,\"IPV4V6\",\"access_point_name\",\"0.0.0.0\",0,0",
        "",
        "OK",
        ""
      ],
      'AT$QCPDPP?': [
        "(ECHO_BACK)",
        "",
        "",
        "$QCPDPP: 1,3,\"user_id\"",
        "$QCPDPP: 2,0",
        "$QCPDPP: 3,0",
        "$QCPDPP: 4,0",
        "$QCPDPP: 5,0",
        "$QCPDPP: 6,0",
        "$QCPDPP: 7,0",
        "$QCPDPP: 8,0",
        "$QCPDPP: 9,0",
        "$QCPDPP: 10,0",
        "$QCPDPP: 11,0",
        "$QCPDPP: 12,0",
        "$QCPDPP: 13,0",
        "$QCPDPP: 14,0",
        "$QCPDPP: 15,0",
        "$QCPDPP: 16,0",
        "",
        "OK",
        ""
      ],
      'AT+CGDCONT=': [
        "(ECHO_BACK)",
        "",
        "",
        "OK",
        ""
      ],
      'AT$QCPDPP=': [
        "(ECHO_BACK)",
        "",
        "",
        "OK",
        ""
      ],
      'AT+CSQ': [
        "(ECHO_BACK)",
        "",
        "",
        "+CSQ: 4,99", # "+CSQ: 99,99"
        "",
        "OK",
        ""
      ],
      'AT+CNUM': [
        "(ECHO_BACK)",
        "",
        "",
        "+CNUM: ,\"09099999999\",129", # "+CNUM: ,\"\",129"
        "",
        "OK",
        ""
      ],
      'AT+CIMI': [
        "(ECHO_BACK)",
        "",
        "",
        "440111111111111", # "+CME ERROR: operation not allowed"
        "",
        "OK",
        ""
      ],
      'AT+CPAS': [
        "(ECHO_BACK)",
        "",
        "",
        "+CPAS: 4", # "+CPAS: 0"
        "",
        "OK",
        ""
      ],
      'ATI': [
        "(ECHO_BACK)",
        "",
        "",
        "Manufacturer: MAN",
        "Model: MOD",
        "Revision: REV",
        "IMEI: 999999999999999",
        "+GCAP: +CGSM",
        "",
        "OK",
        ""
      ]
    }

  def read_line(self):
    if self.line < 0:
      return None
    try:
      text = self.res[self.cmd][self.line]
      self.line += 1
      return text
    except:
      self.line = -1
      return None

  def write(self, str):
    print("W:[%s]" % str)
    self.cmd = str.strip()
    if self.cmd.find('=') >= 0:
      self.cmd = self.cmd[:self.cmd.find('=') + 1]
    self.line = 0
    self.res[self.cmd][0] = str.strip()
