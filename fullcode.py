from microbit import *
import speech
import utime as time

from ssd1306 import initialize, clear_oled
from ssd1306_text import add_text
from ssd1306_img import create_stamp
from ssd1306_stamp import draw_stamp

choose = 0
confirm = False
begin = True

R = pin8
G = pin9
stamp1 = create_stamp(Image.HAPPY)
stamp2 = create_stamp(Image.SAD)
stamp3 = create_stamp(Image.CONFUSED)

udata = " "
agegroup = " "
gender = " "
previous = []
user = 0

window = []
threshold = 0
count = 0
sample = 0
beat = False
start = True
values = []

initialize()
clear_oled()


def getrange(x, y):  # according to age group and gender
    a = 0  # get noraml range of bpm
    b = 0
    if x == "male":
        if y == "12-19":
            a = 72
            b = 77
        elif (y == "20-39") or (y == "40-59"):
            a = 68
            b = 73
        elif y == "above 60":
            a = 66
            b = 71
        elif y == "4-11":
            a = 80
            b = 94
        else:
            a = 106
            b = 128
    else:
        if y == "12-19":
            a = 78
            b = 83
        elif y == "20-39":
            a = 74
            b = 79
        elif (y == "40-59") or (y == "above_60"):
            a = 70
            b = 75
        else:
            a = 108
            b = 129
    return a, b


def showresult(n):
    if user == 1:
        hbrange = getrange(udata[user], udata[user - 1])
    else:
        hbrange = getrange(udata[user], udata[user + 2])
    a = hbrange[0]
    b = hbrange[1]
    if (n >= a) and (b >= n):
        G.write_analog(1023)
        add_text(0, 3, "healthy")
        draw_stamp(30, 15, stamp1, 1)
        speech.say("You are healthy.", speed=90, pitch=60)
    elif (abs(a - n) <= 13) or (abs(b - n) <= 13):
        G.write_analog(1023)
        R.write_analog(1023)
        add_text(0, 3, "Normal")
        draw_stamp(30, 15, stamp3, 1)
        speech.say("You are normal.", speed=90, pitch=60)
    else:
        R.write_analog(1023)
        add_text(0, 3, "unhealthy")
        speech.say("You are unhealthy.", speed=90, pitch=60)
        draw_stamp(30, 15, stamp2, 1)


def mean(datalist):
    sum = 0
    for i in datalist:
        sum += i
    if len(datalist) > 0:
        return sum / len(datalist)
    else:
        return None


while True:
    # get data from udata
    if begin:
        with open("udata.txt", "rt") as f:
            udata = (f.read()).split(" ")
        print(udata)
        with open("previous.txt", "rt") as g:
            previous = (g.read()).split(" ")
        print(previous)
        if len(previous) == 5:
            previous.pop(4)
        begin = False
    # choosing mode
    while confirm is False:
        if button_a.was_pressed():
            choose += 1
        selected = choose % 4 + 1
        display.show(str(selected))
        if selected == 1:
            add_text(0, 1, "Mode 1:")
            add_text(0, 2, "efficient")
        if selected == 2:
            add_text(0, 1, "Mode 2:")
            add_text(0, 2, "accurate ")
        if selected == 3:
            add_text(0, 1, "Mode 3:")
            add_text(0, 2, "User data")
        if selected == 4:
            add_text(0, 1, "Mode 4:")
            add_text(0, 2, "record")
        if button_b.was_pressed():
            mode = selected
            clear_oled()
            if (mode == 3) or (mode == 4):
                choose = 0
                clear_oled()
                confirm = True
            else:
                add_text(0, 0, "which user")
                while not button_b.was_pressed():
                    if button_a.was_pressed():
                        choose += 1
                    selected = choose % 3 + 1
                    display.show(str(selected))
                    if selected == 1:
                        add_text(0, 1, "user 1")
                    if selected == 2:
                        add_text(0, 1, "user 2")
                    if selected == 3:
                        add_text(0, 1, "user 3")
                user = selected
                add_text(0, 0, "put your")
                add_text(0, 1, "finger")
                add_text(0, 2, "in sensor")
                sleep(3000)
                clear_oled()
                add_text(0, 1, "adjusting")
                add_text(0, 2, "threshold")
                while threshold == 0:  # if mode 1 or mode 2, detect threshold first
                    signal = pin0.read_analog()
                    window.append(signal)
                    if len(window) == 20:  # sample 20 times, save mean once
                        avg = round(mean(window))  # otherwise not enough memory
                        window = []
                        values.append(avg)
                    sample += 1
                    if sample == 200:
                        threshold = mean(values)
                        values = []
                        window = []
                        sample = 0
                        bpm = 0
                        sleep(20)
                        confirm = True
                        clear_oled()
                        add_text(0, 2, "detecting")
                    sleep(10)
    # mode 1
    while confirm and (mode == 1):
        signal = pin0.read_analog()
        window.append(signal)
        avg = round(mean(window))
        if len(window) == 11:
            window.pop(0)
        if beat is False and avg >= threshold + 10:
            beat = True
            count += 1
            display.show(Image.HEART, wait=False)
            if count == 1:
                t1 = time.ticks_ms()
            if count == 11:
                t2 = time.ticks_ms()
                bpm = round(600 * 1000 / (t2 - t1))
                clear_oled()
                display.scroll(str(bpm))
                add_text(0, 0, "Heart rate:")
                add_text(2, 1, str(bpm))
                if udata[user] != "":  # no user data, then no result, only show bpm
                    showresult(bpm)
                previous.append(str(user) + str(bpm))
                if len(previous) == 5:
                    previous.pop(0)
                with open("previous.txt", "w") as f:
                    for i in previous:
                        if i != "":
                            f.write(i + " ")
                count = 0
                threshold = 0
                window = []
                sleep(10000)
                clear_oled()
                G.write_analog(0)
                R.write_analog(0)
                confirm = False
        elif beat is True and avg <= threshold - 10:
            beat = False
            display.clear()
        # udata[2] = str(bpm).strip()
        sleep(20)

    # mode 2
    if confirm and (mode == 2):
        if start:
            t1 = time.ticks_ms()
            t2 = time.ticks_ms()
            clear_oled()
            add_text(0, 0, "time:")
        while t2 - t1 < 60000:
            t2 = time.ticks_ms()
            signal = pin0.read_analog()
            window.append(signal)
            avg = round(mean(window))
            if len(window) == 11:
                window.pop(0)
            if beat is False and avg >= threshold + 10:
                beat = True
                bpm += 1
                display.show(Image.HEART, wait=False)
            elif beat is True and avg <= threshold - 10:
                beat = False
                display.clear()
            if ((t2 - t1) % 1000) == 0:
                add_text(2, 2, " " + str(60 - (t2 - t1) // 1000) + " ")
        clear_oled()
        display.scroll(str(bpm))
        add_text(0, 0, "Heart rate:")
        add_text(2, 1, str(bpm))
        if udata[user] != "":  # no user data, then no result, only show bpm
            showresult(bpm)
        previous.append(str(user) + str(bpm))
        if len(previous) == 5:
            previous.pop(0)
        with open("previous.txt", "w") as f:
            for i in previous:
                if i != "":
                    f.write(i + " ")
        threshold = 0
        window = []
        sleep(10000)
        clear_oled()
        G.write_analog(0)
        R.write_analog(0)
        confirm = False
    # mode 3
    if confirm and (mode == 3):
        while not button_b.was_pressed():
            if button_a.was_pressed():
                choose += 1
            selected = choose % 3 + 1
            if selected == 1:
                add_text(0, 0, "user 1  ")
                if udata[1] == "":
                    add_text(0, 1, "sex: NA        ")
                    add_text(0, 2, "age: NA        ")
                else:
                    add_text(0, 1, "sex: " + udata[1] + "   ")
                    add_text(0, 2, "age: " + udata[0] + "   ")
            if selected == 2:
                add_text(0, 0, "user 2  ")
                if udata[2] == "":
                    add_text(0, 1, "sex: NA         ")
                    add_text(0, 2, "age: NA         ")
                else:
                    add_text(0, 1, "sex: " + udata[2] + "   ")
                    add_text(0, 2, "age: " + udata[4] + "   ")
            if selected == 3:
                add_text(0, 0, "user 3  ")
                if udata[3] == "":
                    add_text(0, 1, "sex: NA         ")
                    add_text(0, 2, "age: NA         ")
                else:
                    add_text(0, 1, "sex: " + udata[3] + "   ")
                    add_text(0, 2, "age: " + udata[5] + "   ")
        user = selected
        sleep(3000)
        if button_b.was_pressed():
            clear_oled()
            add_text(0, 0, "age group")
            add_text(0, 2, "A change")
            add_text(0, 3, "B confirm")
            while not button_b.was_pressed():  # choose age group
                if button_a.was_pressed():
                    choose += 1
                selected = choose % 6 + 1
                if selected == 1:
                    agegroup = "1-3         "
                    add_text(0, 1, agegroup)
                if selected == 2:
                    agegroup = "4-11        "
                    add_text(0, 1, agegroup)
                if selected == 3:
                    agegroup = "12-19       "
                    add_text(0, 1, agegroup)
                if selected == 4:
                    agegroup = "20-39       "
                    add_text(0, 1, agegroup)
                if selected == 5:
                    agegroup = "40-59       "
                    add_text(0, 1, agegroup)
                if selected == 6:
                    agegroup = "above60     "
                    add_text(0, 1, agegroup)
            add_text(0, 0, "your sex")
            while not button_b.was_pressed():  # choose gender
                if button_a.was_pressed():
                    choose += 1
                selected = choose % 2 + 1
                if selected == 1:
                    gender = "male        "
                    add_text(0, 1, gender + "   ")
                if selected == 2:
                    gender = "female      "
                    add_text(0, 1, gender + "   ")
            if user == 1:
                udata[1] = gender.strip()
                udata[0] = agegroup.strip()
            elif user == 2:
                udata[2] = gender.strip()
                udata[4] = agegroup.strip()
            elif user == 3:
                udata[3] = gender.strip()
                udata[5] = agegroup.strip()
            with open("udata.txt", "w") as f:  # save user data in udata file
                for i in range(6):
                    f.write(udata[i] + " ")
        selected = 0
        clear_oled()
        confirm = False
    if confirm and (mode == 4):
        if len(previous) > 1:
            for i in range(len(previous)):
                if previous[i] != "":
                    s = previous[i]
                    add_text(0, i, str(i + 1) + ". " + "user" + s[0] + " " + s[1:3])
        else:
            add_text(0, 0, "No record")
        sleep(3000)
        selected = 0
        clear_oled()
        confirm = False
