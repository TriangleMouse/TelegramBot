# import sqlite3
import pymysql


class DataBase_Requests:
    def __init__(self, connect):
        """Подключаемся к БД и сохраняем курсор соединения"""
        self.connection = connect
        self.cursor = self.connection.cursor()

    def get_telegram_id(self, bxb_user_id):
        """Получаем id подписчика бота для отправки сообщения о совершении сделки"""
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM `tg_subscriptions` WHERE `bxb_user_id` = %s", bxb_user_id)
            return cursor.fetchall()

    def get_user(self, tg_user_id):
        """Получаем данные о пользователе бота"""
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM `tg_subscriptions` WHERE `tg_user_id` = %s", tg_user_id)
            return cursor.fetchall()

    def subscriber_exists(self, tg_user_id):
        """Проверяем, есть ли уже юзер в базе"""
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM `tg_subscriptions` WHERE `tg_user_id` = %s", tg_user_id)
            return bool(len(cursor.fetchall()))

    def update_temporary_key(self, tg_user_id, temporary_key):
        """Обновляем временный ключ пользователя"""
        with self.connection.cursor() as cursor:
            return cursor.execute("UPDATE `tg_subscriptions` SET `temporary_key` = %s WHERE `tg_user_id` = %s",
                                  (temporary_key, tg_user_id))

    def update_tg_lang(self, tg_user_id, tg_lang):
        """Обновляем язык пользователя"""
        with self.connection.cursor() as cursor:
            return cursor.execute("UPDATE `tg_subscriptions` SET `tg_lang` = %s WHERE `tg_user_id` = %s",
                                  (tg_lang, tg_user_id))

    def update_taker_switch(self, tg_user_id, taker_permission):
        """Обновляем  Taker(будет ли юзер получать информацию о Taker сделках))"""
        with self.connection.cursor() as cursor:
            return cursor.execute("UPDATE `tg_subscriptions` SET `taker_permission` = %s WHERE `tg_user_id` = %s",
                                  (taker_permission, tg_user_id))

    def update_bxb_user_id(self, tg_user_id, bxb_user_id, menu_permission=True):
        """Обновляем бхб id пользователя и даем доступ к меню"""
        with self.connection.cursor() as cursor:
            return cursor.execute("UPDATE `tg_subscriptions` SET `bxb_user_id` = %s, `menu_permission` = %s WHERE "
                                  "`tg_user_id` = %s", (bxb_user_id, menu_permission, tg_user_id))

    def update_username__tmp_key(self, tg_user_id, tg_username, temporary_key):
        """Обновляем имя  пользователя и временный ключ"""
        with self.connection.cursor() as cursor:
            return cursor.execute(
                "UPDATE `tg_subscriptions` SET `tg_username` = %s,`temporary_key` = %s WHERE `tg_user_id` = %s",
                (tg_username, temporary_key, tg_user_id))

    def update_tg_username(self, tg_user_id, tg_username):
        """Обновляем имя пользователя"""
        with self.connection.cursor() as cursor:
            return cursor.execute("UPDATE `tg_subscriptions` SET `tg_username` = %s WHERE `tg_user_id` = %s",
                                  (tg_username, tg_user_id))

    def add_subscriber(self, tg_user_id, tg_username, temporary_key):
        """Добавляем нового подписчика"""
        with self.connection.cursor() as cursor:
            return cursor.execute(
                "INSERT INTO `tg_subscriptions` (`tg_user_id`, `tg_username`, `temporary_key`) "
                "VALUES(%s,%s,%s)", (tg_user_id, tg_username, temporary_key)
            )

    def delete_subscriber(self, tg_user_id):
        """Удаляе пользователя"""
        with self.connection.cursor() as cursor:
            return cursor.execute("DELETE FROM `tg_subscriptions` WHERE `tg_user_id`= %s", tg_user_id)

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()
