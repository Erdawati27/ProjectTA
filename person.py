class Person:
    def __init__(self, prs_nbr,prs_name, prs_address, prs_no_hp, prs_active, prs_added, mysql):
        self.prs_nbr = prs_nbr
        self.prs_name = prs_name
        self.prs_address = prs_address
        self.prs_active = prs_active
        self.prs_added = prs_added
        self.prs_no_hp = prs_no_hp
        self.mysql = mysql

    def add(self):
        cur = self.mysql.connection.cursor()
        cur.execute("INSERT INTO `prs_mstr` (`prs_nbr`, `prs_name`, `prs_address`, `prs_no_hp`) VALUES (%s, %s, %s, %s)", (self.prs_nbr, self.prs_name, self.prs_address, self.prs_no_hp))
        self.mysql.connection.commit()
        cur.close()

    @staticmethod
    def get_prsn(id,mysql):
        cur = mysql.connection.cursor()
        cur.execute("select `prs_nbr`, `prs_name`, `prs_address`, `prs_no_hp`, prs_active, prs_added from prs_mstr where prs_nbr= "+ str(id))
        data = cur.fetchall()
        return data
    def list_prsn(mysql):
        cur = mysql.connection.cursor()
        cur.execute("select `prs_nbr`, `prs_name`, `prs_address`, `prs_no_hp`, prs_active, prs_added "
                         "from prs_mstr "
                         "where prs_active = 1 "
                         " order by prs_nbr desc")
        data = cur.fetchall()
        return data

