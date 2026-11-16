;;; Лабораторна №4, Етап 1 (AutoCAD): цифра «8» з написами ПІБ.
;;; Ті самі кроки, що в docs/guide.md, але без ручного виділення шарів:
;;;   APKS2D - REGION для всіх контурів (знімок acad_2d.png)
;;;   APKS3D - EXTRUDE / SUBTRACT / UNION, ізометрія, MASSPROP (знімок acad_3d.png)
;;; Запуск: відкрити dxf/digit8_full.dxf, APPLOAD -> цей файл, далі APKS2D, потім APKS3D.

(defun apks:ss (lay typ) (ssget "_X" (list (cons 0 typ) (cons 8 lay))))

;; REGION і EXTRUDE кладуть результат на поточний шар, тому нові об'єкти
;; повертаємо на шар вихідних контурів (за шарами далі йде вибір для UNION / SUBTRACT).
(defun apks:since (e / new)
  (setq new (ssadd))
  (if e (while (setq e (entnext e)) (ssadd e new))
        (if (setq e (entnext)) (progn (ssadd e new) (while (setq e (entnext e)) (ssadd e new)))))
  new)

(defun apks:onlayer (new lay)
  (if (> (sslength new) 0) (command "_.CHPROP" new "" "_LA" lay "")))

(defun apks:region (lay / s e)
  (if (setq s (apks:ss lay "LWPOLYLINE"))
    (progn
      (setq e (entlast))
      (command "_.REGION" s "")
      (apks:onlayer (apks:since e) lay))))

;; Видавлює регіони шару на h (з попереднім зсувом на dz) і повертає набір тіл цього шару.
(defun apks:extrude (lay dz h / s e)
  (if (setq s (apks:ss lay "REGION"))
    (progn
      (if (/= dz 0) (command "_.MOVE" s "" "0,0,0" (strcat "0,0," (rtos dz 2 3))))
      (setq e (entlast))
      (command "_.EXTRUDE" s "" h)
      (apks:onlayer (apks:since e) lay)))
  (apks:ss lay "3DSOLID"))

;; Тіла шару NAME_OUTER мінус тіла NAME_HOLES (дірки в літерах О, Р, А, Б, Д, В).
(defun apks:letters (name dz h / o i)
  (setq o (apks:extrude (strcat name "_OUTER") dz h)
        i (apks:extrude (strcat name "_HOLES") dz h))
  (if (and o i) (command "_.SUBTRACT" o "" i ""))
  (apks:ss (strcat name "_OUTER") "3DSOLID"))

(defun c:APKS2D ()
  (setvar "CMDECHO" 0) (setvar "OSMODE" 0)
  (foreach n '("DIGIT" "SURNAME" "NAME" "PATRONYMIC")
    (apks:region (strcat n "_OUTER"))
    (apks:region (strcat n "_HOLES")))
  (command "_.ZOOM" "_E") (command "_.ZOOM" "0.8x")
  (princ (strcat "\nРегіонів: " (itoa (sslength (ssget "_X" '((0 . "REGION")))))))
  (princ))

(defun c:APKS3D (/ digit s)
  (setvar "CMDECHO" 0) (setvar "OSMODE" 0) (setvar "DELOBJ" 1)
  ;; 1. Тіло цифри: EXTRUDE 10, SUBTRACT два вікна
  (setq digit (apks:letters "DIGIT" 0 10))
  ;; 2. Прізвище: опукле, +2 мм над верхньою гранню -> UNION
  (setq s (apks:letters "SURNAME" 10 2))
  (command "_.UNION" digit s "")
  ;; 3. Ім'я: увігнуте, -1.5 мм від верхньої грані -> SUBTRACT
  (setq s (apks:letters "NAME" 10 -1.5))
  (command "_.SUBTRACT" (apks:ss "DIGIT_OUTER" "3DSOLID") "" s "")
  ;; 4. По батькові: наскрізне, від -1 на 12 мм -> SUBTRACT
  (setq s (apks:letters "PATRONYMIC" -1 12))
  (command "_.SUBTRACT" (apks:ss "DIGIT_OUTER" "3DSOLID") "" s "")
  ;; Вигляд і контроль об'єму (очікувано ~81 000 мм3, як у gen_stl.py)
  (command "_.-VIEW" "_SWISO")
  (command "_.VSCURRENT" "_R")
  (command "_.ZOOM" "_E") (command "_.ZOOM" "0.8x")
  (command "_.MASSPROP" (apks:ss "DIGIT_OUTER" "3DSOLID") "")
  (princ))

(princ "\nAPKS: команди APKS2D і APKS3D завантажено.")
(princ)
