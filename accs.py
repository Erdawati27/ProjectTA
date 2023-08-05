from person import Person
from flask_mysqldb import MySQL
class Acces:
    def __init__(self,accs_id, accs_date,accs_prsn,accs_added, accs_tujuan, mysql):
        self.accs_id = accs_id
        self.accs_date = accs_date
        self.accs_prsn = accs_prsn
        self.accs_added = accs_added
        self.accs_tujuan = accs_tujuan
        self.mysql = mysql

    def recAccs(self):
        cur = self.mysql.connection.cursor()
        cur.execute(
            "INSERT INTO accs_hist (accs_date, accs_prsn,accs_tujuan) VALUES (%s, %s, %s)",
            (self.accs_date, self.accs_prsn, self.accs_tujuan))
        self.mysql.connection.commit()
        cur.close()
    def update_accs(self):
        cur = self.mysql.connection.cursor()
        cur.execute(
            "UPDATE `accs_hist` SET `accs_date`=%s, `accs_prsn`=%s, `accs_added`=%s, `accs_tujuan`=%s WHERE accs_id = %s",
            (self.accs_date, self.accs_prsn, self.accs_added, self.accs_tujuan, self.accs_id))
        self.mysql.connection.commit()

    @staticmethod
    def get_list_accs(mysql):
        cur = mysql.connection.cursor()
        cur.execute(
            "select a.accs_id, a.accs_prsn, b.prs_name, b.prs_address, b.prs_no_hp,date_format(a.accs_date, '%D/%M/%Y'), date_format(a.accs_added, '%H:%i:%s') "
            "  from accs_hist a "
            "  left join prs_mstr b on a.accs_prsn = b.prs_nbr "
            " order by a.accs_id desc")
        data = cur.fetchall()
        cur.close()
        if data:
            return data
        return data
    def get_accs_data(id,mysql):
        cur = mysql.connection.cursor()
        cur.execute("select a.accs_id, a.accs_prsn, a.accs_tujuan, b.prs_name, b.prs_address, b.prs_no_hp,date_format(a.accs_date, '%D/%M/%Y'), date_format(a.accs_added, '%H:%i:%s') "
        "  from accs_hist a "
        "  left join prs_mstr b on a.accs_prsn = b.prs_nbr "
        " where a.accs_id = "+str(id))
        data = cur.fetchone()
        cur.close()
        if data:
            return data
        return data
    def select_date(id,mysql):
        cur = mysql.connection.cursor()
        cur.execute("select accs_date,accs_added from accs_hist where accs_id =" + id)
        row = cur.fetchone()
        return row