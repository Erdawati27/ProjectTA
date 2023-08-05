import sys

class Image:
    def __init__(self, img_id, img_person, mysql):
        self.img_person = img_person
        self.img_id = img_id
        self.mysql = mysql

    @staticmethod
    def get_img(id,mysql):
        cur = mysql.connection.cursor()
        cur.execute('select * from img_dataset where `img_person`=' + id + ' limit 1')
        data = cur.fetchall()
        print(data)
        return data