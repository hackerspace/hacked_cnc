
def load_calibration_matrix(filename):

    map =  list()
    with open(filename) as fd:
        for line in fd:
            cols = line.strip().split(',')

            items = list()
            for col in cols:
                item = list()
                #print(col)
                for i in col.strip().split(' '):
                    #print(i)
                    item.append(float(i))
                items.append(item)

            map.append(items)

    return map

def load_gcode_commands(filename):

    commands = list()

    with open(filename) as fd:

        prev_cmnd = {"cmd": 'shit', 'X': 0, 'Y': 0, 'Z': 0, 'L': 0}

        for line in fd:

            parts = line.strip().split(' ')
            gcode, parts = parts[0], parts[1:]
            #print(gcode, parts)
            command = {"cmd": gcode}

            for part in parts:
                if part == '':
                    continue
                if part.startswith('('):
                    break
                command[part[0]] = part[1:]

            for axis in "XYZL":
                if axis not in command:
                    command[axis] = prev_cmnd[axis]

            commands.append(command)

            prev_cmnd = command


    return commands
