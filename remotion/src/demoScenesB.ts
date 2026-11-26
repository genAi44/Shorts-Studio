// Split from demo.ts: demo scenes 7-12.
export const demoScenesB: unknown[] = [
    {
      "id": "sc_7",
      "role": "body",
      "from": 630,
      "dur": 90,
      "words": [
        {
          "t": "ركائز",
          "s": 0.1,
          "e": 0.4
        },
        {
          "t": "الدولة",
          "s": 0.5,
          "e": 0.8
        },
        {
          "t": "البوليفية",
          "s": 0.9,
          "e": 1.2
        }
      ],
      "beats": [
        {
          "kind": "icons",
          "title": "ركائز الدولة البوليفية",
          "items": [
            {
              "icon": "mountain",
              "label": "الجبال"
            },
            {
              "icon": "building",
              "label": "الحكومة"
            },
            {
              "icon": "coin",
              "label": "الثروة"
            },
            {
              "icon": "people",
              "label": "الشعب"
            }
          ],
          "from": 0,
          "dur": 90
        }
      ]
    },
    {
      "id": "sc_8",
      "role": "body",
      "from": 720,
      "dur": 90,
      "words": [
        {
          "t": "رمزية",
          "s": 0.1,
          "e": 0.4
        },
        {
          "t": "السيادة",
          "s": 0.5,
          "e": 0.8
        },
        {
          "t": "الوطنية",
          "s": 0.9,
          "e": 1.2
        }
      ],
      "beats": [
        {
          "kind": "canvas",
          "title": "رمزية السيادة الوطنية",
          "elements": [
            {
              "type": "icon",
              "name": "flag",
              "x": 540,
              "y": 700,
              "size": 220,
              "color": "accent",
              "enter": "pop"
            },
            {
              "type": "text",
              "text": "دولة واحدة بعاصمتين",
              "x": 540,
              "y": 1000,
              "size": 68,
              "color": "text",
              "enter": "rise"
            },
            {
              "type": "shape",
              "shape": "ring",
              "x": 540,
              "y": 700,
              "size": 280,
              "color": "accent2",
              "enter": "pop"
            }
          ],
          "from": 0,
          "dur": 90
        }
      ]
    },
    {
      "id": "sc_9",
      "role": "body",
      "from": 810,
      "dur": 90,
      "words": [
        {
          "t": "قصر",
          "s": 0.1,
          "e": 0.4
        },
        {
          "t": "الحكومة",
          "s": 0.5,
          "e": 0.8
        },
        {
          "t": "التاريخي",
          "s": 0.9,
          "e": 1.2
        }
      ],
      "beats": [
        {
          "kind": "photo",
          "title": "قصر الحكومة التاريخي",
          "src": "sample_photo.jpg",
          "credit": "Wikimedia Commons",
          "camera": "push-in",
          "from": 0,
          "dur": 90
        }
      ]
    },
    {
      "id": "sc_10",
      "role": "body",
      "from": 900,
      "dur": 90,
      "words": [
        {
          "t": "توزيع",
          "s": 0.1,
          "e": 0.4
        },
        {
          "t": "الاختصاصات",
          "s": 0.5,
          "e": 0.8
        }
      ],
      "beats": [
        {
          "kind": "split",
          "title": "توزيع الاختصاصات",
          "left": {
            "title": "القضاء الدستوري",
            "value": "سوكري",
            "sub": "المقر التاريخي",
            "icon": "book"
          },
          "right": {
            "title": "السلطة التنفيذية",
            "value": "لاباز",
            "sub": "مقر الرئاسة",
            "icon": "crown"
          },
          "from": 0,
          "dur": 90
        }
      ]
    },
    {
      "id": "sc_11",
      "role": "body",
      "from": 990,
      "dur": 90,
      "words": [
        {
          "t": "بيانات",
          "s": 0.1,
          "e": 0.4
        },
        {
          "t": "جغرافية",
          "s": 0.5,
          "e": 0.8
        },
        {
          "t": "حاسمة",
          "s": 0.9,
          "e": 1.2
        }
      ],
      "beats": [
        {
          "kind": "ticker",
          "title": "بيانات جغرافية حاسمة",
          "items": [
            {
              "text": "لاباز أعلى مقر حكومي في العالم",
              "icon": "mountain"
            },
            {
              "text": "سوكري العاصمة الدستورية منذ 1825",
              "icon": "home"
            },
            {
              "text": "عدد السكان يتجاوز 12 مليون نسمة",
              "icon": "people"
            }
          ],
          "from": 0,
          "dur": 90
        }
      ]
    },
    {
      "id": "sc_12",
      "role": "body",
      "from": 1080,
      "dur": 90,
      "words": [
        {
          "t": "المحطات",
          "s": 0.1,
          "e": 0.4
        },
        {
          "t": "الرئيسية",
          "s": 0.5,
          "e": 0.8
        }
      ],
      "beats": [
        {
          "kind": "cardstack",
          "title": "المحطات الرئيسية",
          "items": [
            {
              "text": "استقلال بوليفيا عام 1825",
              "value": "1825",
              "icon": "scale"
            },
            {
              "text": "نقل البرلمان إلى لاباز",
              "value": "1899",
              "icon": "building"
            },
            {
              "text": "إقرار الدستور التعددي",
              "value": "2009",
              "icon": "book"
            }
          ],
          "from": 0,
          "dur": 90
        }
      ]
    }
];
