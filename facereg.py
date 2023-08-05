from flask_mysqldb import MySQL
class FaceReg:
    def __init__(self, accs_date,accs_prsn, mysql,app):
        self.accs_date = accs_date
        self.accs_prsn = accs_prsn
        self.mysql = mysql
        self.app = app

    def RecAccs(self):
        # print(self.mysql)
        with self.app.app_context():
            cur = self.mysql.connection.cursor()
            cur.execute("insert into accs_hist (accs_date, accs_prsn) values('" + str(
                self.accs_date) + "', '" + self.accs_prsn + "')")
            self.mysql.connection.commit()
            cur.close()



