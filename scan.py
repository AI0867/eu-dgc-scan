#!/usr/bin/env python

import base45
import cbor
import cose.messages
import cv2
import pyzbar.pyzbar
import sys

MA_MAP = {
    'ORG-100030215'     : 'Pfizer',
}
MP_MAP = {
    'EU/1/20/1528'      : 'Comirnaty',
}

go_grey = False

cap = cv2.VideoCapture(0)
cap.set(3,640)
cap.set(4,480)

cap.open(0)

known_codes = set()

verbose = len(sys.argv) > 1 and sys.argv[1] == '-v'

while cap.isOpened():
    success, img = cap.read()
    if success:
        if go_grey:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        codes = pyzbar.pyzbar.decode(img)
        for decoded_code in codes:
            if verbose:
                print(decoded_code)
            # Stuff about visualization
            if len(decoded_code.polygon) > 4:
                reduced = numpy.squeeze(cv2.convexHull(numpy.array(decoded_code.polygon)))
                [tuple(point) for point in reduced]
            else:
                hull = decoded_code.polygon
            for vertex in range(len(hull)):
                cv2.line(img, hull[vertex], hull[(vertex + 1) % len(hull)], (255, 0, 0), 3)

            # Stuff about decoding
            code = decoded_code.data
            if code not in known_codes:
                known_codes.add(code)
                if verbose:
                    print(f"Found QR code: {code}")
                b45 = base45.b45decode(code[4:])
                if verbose:
                    print(f"Base45 decoded: {b45}")
                cosemsg = cose.messages.Sign1Message.decode(b45[7:])
                if verbose:
                    print(f"COSE message: {cosemsg}")
                    print(f"Payload: {cosemsg.payload}")
                json = cbor.loads(cosemsg.payload)
                if verbose:
                    print(f"CBOR decoded: {json}")
                print(f"Country: {json[1]}")
                about = json[-260][1]
                for key in json.keys():
                    if key not in [1,4,6,-260]:
                        print(f"Unknown key found in CBOR: {key}, value: {json[key]}")
                for key in json[-260].keys():
                    if key not in [1]:
                        print(f"Unknown key found in CBOR[-260]: {key}, value: {json[-260][key]}")
                for key in json[-260][1].keys():
                    if key not in ['ver','dob','nam','v']:
                        print(f"Unknown key found in CBOR[-260][1]: {key}, value: {json[-260][1][key]}")
                print(f"QR code version {about['ver']}")
                for key in json[-260][1]['nam']:
                    if key not in ['gn', 'gnt', 'fn', 'fnt']:
                        print(f"Unknown key found in CBOR[-260][1]['nam']: {key}, value: {json[-260][1]['nam'][key]}")
                print(f"For {about['nam']['gn']} {about['nam']['fn']} AKA {about['nam']['gnt']} {about['nam']['fnt']} born on {about['dob']}")
                print(f"We found {len(about['v'])} vaccinations:")
                for i, vac in enumerate(about['v']):
                    for key in vac.keys():
                        if key not in ['tg', 'vp', 'mp', 'ma', 'dn', 'sd', 'dt', 'co', 'is', 'ci']:
                            print(f"Unknown key found in vaccination: {key}, value: {vac[key]}")
                    manufacturer = f"{MA_MAP[vac['ma']]} ({vac['ma']})" if vac['ma'] in MA_MAP else vac['ma']
                    vaccine = f"{MP_MAP[vac['mp']]} ({vac['mp']})" if vac['mp'] in MP_MAP else vac['mp']
                    # TODO check meaning of rest
                    print(f"{i+1}: On {vac['dt']}, you received {vaccine} made by {manufacturer} from {vac['is']} in {vac['co']}")
                    # TODO: tg, vp, dn, sd, ci
    cv2.imshow('frame', img)
    key = cv2.waitKey(1)
    if key & 0xFF == ord('q'):
        break
    elif key & 0xFF == ord(' '):
        go_grey = not go_grey

cap.release()
cv2.destroyAllWindows()
