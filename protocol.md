# מסמך תכנון פרוטוקול תקשורת - SQL_HTML (Pokemon Theme)

## 1. ארכיטקטורה ואבטחה (Encryption & Handshake)

התקשורת בין הלקוח והשרת מבוססת על TCP ועוברת דרך מנגנון אבטחה בשני שלבים:

### א. תהליך Handshake והחלפת מפתחות
1. **חיבור ראוני**: הלקוח מתחבר לשרת ושולח הודעה: `KEY_METHOD|RSA`.
2. **אישור שרת**: השרת מחזיר `SUPPORTED`.
3. **שליחת מפתח ציבורי**: השרת שולח ללקוח את המפתח הציבורי שלו מסוג RSA (באורך 2048 ביט, פורמט PEM).
4. **יצירת מפתח סימטרי**: הלקוח מייצר מפתח סימטרי רנדומלי מסוג AES (באורך 256 ביט).
5. **הצפנת המפתח ושליחתו**: הלקוח מצפין את מפתח ה-AES באמצעות המפתח הציבורי של השרת (בעזרת RSA-OAEP עם SHA256) ושולח אותו לשרת.
6. **פענוח השרת**: השרת מפענח את המפתח הסימטרי בעזרת המפתח הפרטי שלו (`private_key.pem`).
7. **פתיחת סשן מאובטח**: מכאן ואילך, שני הצדדים משתמשים באובייקט `SecureSession` המבצע הצפנת AES-GCM (עם Nonce אקראי באורך 12 בתים המצורף בתחילת כל הודעה).

### ב. אימות משתמשים (Salt & Pepper)
- לכל משתמש נוצר **Salt** אקראי ייחודי (8 תווים).
- במערכת מוגדר **Pepper** סודי קבוע (הנשמר בקובץ `pepper.txt`).
- הסיסמה הנשמרת ב-DB מחושבת בצורה הבאה:
  `hashed_password = SHA256(password + salt + PEPPER)`

### ג. מעטפת ההודעות (Framing)
כל הודעה נשלחת דרך מודול `tcp_by_size`: תקדומת באורך 9 תווים המייצגת את גודל ההודעה (`000000000|`) ולאחריה התוכן המוצפן.

---

## 2. מבנה ההודעות (Message Protocol)

- **פורמט בקשת לקוח**: `ACTION|param1|param2|...`
- **פורמט תשובת שרת**: `RESPONSE_ACTION|STATUS|data1|data2|...`

---

## 3. פירוט 10 השירותים בפרוטוקול

| # | שירות (Action) | פורמט בקשה מהלקוח | פורמט תשובה מהשרת | תיאור |
|---|----------------|-------------------|--------------------|-------|
| 1 | `LOGIN` | `LOGIN\|username\|password` | `LOGIN_RES\|SUCCESS\|account_id` או `LOGIN_RES\|ERR_AUTH` | התחברות מאובטחת עם אימות Hash + Salt + Pepper |
| 2 | `SIGNUP` | `SIGNUP\|username\|password\|email\|phone\|nickname` | `SIGNUP_RES\|SUCCESS\|account_id` או `SIGNUP_RES\|ERR_EXISTS` | הרשמת מאמן פוקימון חדש ויצירת חשבון |
| 3 | `GET_USER` | `GET_USER\|username` | `USER_RES\|SUCCESS\|username\|email\|phone\|account_id` | שליפת פרטי משתמש לפי שם משתמש |
| 4 | `GET_ALL_USERS` | `GET_ALL_USERS` | `ALL_USERS_RES\|SUCCESS\|count\|user1...` | שליפת כל המשתמשים במערכת |
| 5 | `GET_ACCOUNT` | `GET_ACCOUNT\|account_id` | `ACCOUNT_RES\|SUCCESS\|account_id\|nickname\|pokecoins\|pokemons\|level` | שליפת פרטי חשבון פוקימון לפי מזהה |
| 6 | `GET_ALL_ACCOUNTS` | `GET_ALL_ACCOUNTS` | `ALL_ACCOUNTS_RES\|SUCCESS\|count\|acc1...` | שליפת כל חשבונות הפוקימון |
| 7 | `ADD_POKEMON` | `ADD_POKEMON\|account_id\|pokemon_name` | `ADD_POKEMON_RES\|SUCCESS` או `ADD_POKEMON_RES\|ERR` | הוספת פוקימון חדש לחשבון המאמן |
| 8 | `UPDATE_COINS` | `UPDATE_COINS\|account_id\|amount` | `UPDATE_COINS_RES\|SUCCESS\|new_balance` | עדכון יתרת PokéCoins בחשבון |
| 9 | `SEARCH_TRAINER` | `SEARCH_TRAINER\|search_term` | `SEARCH_RES\|SUCCESS\|count\|results...` | חיפוש מאמן (שירות המושאר חשוף ל-SQL Injection לצורך הדגמה) |
| 10 | `DELETE_ACCOUNT` | `DELETE_ACCOUNT\|account_id` | `DELETE_RES\|SUCCESS` או `DELETE_RES\|ERR` | מחיקת חשבון פוקימון |
| 11 | `RULIVE` | `RULIVE` | `RULIVE_RES\|YES` | בדיקת זמינות השרת (Heartbeat) |
| 12 | `LOGOUT` | `LOGOUT` | `LOGOUT_RES\|BYE` | ניתוק הלקוח מהשרת |
