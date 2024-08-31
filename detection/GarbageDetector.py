import cv2
import numpy as np
from tensorflow.lite.python.interpreter import Interpreter
import time
import random

def process_video(input_path, output_path, event_list, selected_cells):

    modelpath = 'detection/detect.tflite'
    lblpath = 'detection/labelmap.txt'
    min_conf = 0.95
    cap = cv2.VideoCapture(input_path)

    interpreter = Interpreter(model_path=modelpath)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]

    float_input = (input_details[0]['dtype'] == np.float32)

    input_mean = 127.5
    input_std = 127.5

    with open(lblpath, 'r') as f:
        labels = [line.strip() for line in f.readlines()]

    object_id = 0
    tracked_objects = {}
    ghost_objects = {}
    color_history = {}
    frame_count = 0
    ghost_frame_limit = 400
    fps = cap.get(cv2.CAP_PROP_FPS)
    start_time = time.time()

    def get_center(box):
        ymin, xmin, ymax, xmax = box
        return (xmin + xmax) // 2, (ymin + ymax) // 2

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (int(cap.get(3)), int(cap.get(4))))

    detected_object_ids = set()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % 4 == 0:

            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imH, imW, _ = frame.shape
            image_resized = cv2.resize(image_rgb, (width, height))
            input_data = np.expand_dims(image_resized, axis=0)

            if float_input:
                input_data = (np.float32(input_data) - input_mean) / input_std

            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()

            boxes = interpreter.get_tensor(output_details[1]['index'])[
                0]  # Coordenadas de las cajas delimitadoras de los objetos detectados
            classes = interpreter.get_tensor(output_details[3]['index'])[0]  # Índice de clase de los objetos detectados
            scores = interpreter.get_tensor(output_details[0]['index'])[0]  # Confianza de los objetos detectados

            detections = []
            new_tracked_objects = {}

            cell_width = imW // 32
            cell_height = imH // 18

            currently_touched_cells = set()

            for i in range(len(scores)):
                if (scores[i] > min_conf) and (scores[i] <= 1.0):
                    ymin = int(max(1, (boxes[i][0] * imH)))
                    xmin = int(max(1, (boxes[i][1] * imW)))
                    ymax = int(min(imH, (boxes[i][2] * imH)))
                    xmax = int(min(imW, (boxes[i][3] * imW)))

                    matched_id = None
                    object_name = labels[int(classes[i])]
                    color = (10, 255, 0)  # Color por defecto (verde)

                    # Verificar si los bordes del objeto tocan las celdas seleccionadas
                    object_touches_selected_cell = False
                    for x in range(xmin, xmax + 1, cell_width):
                        for y in range(ymin, ymax + 1, cell_height):
                            cell_x = x // cell_width
                            cell_y = y // cell_height
                            if (cell_x, cell_y) in selected_cells:
                                object_touches_selected_cell = True
                                currently_touched_cells.add((cell_x, cell_y))

                    # Definir internal_color aunque no se use para la visualización
                    internal_color = color
                    if object_touches_selected_cell:
                        internal_color = (0, 0, 255)  # Rojo si toca una celda seleccionada

                    # Verificar si el objeto actual coincide con algún objeto previamente rastreado
                    for obj_id, obj_data in tracked_objects.items():
                        if object_name == obj_data['name']:
                            prev_center = obj_data['center']
                            if abs((xmin + xmax) / 2 - prev_center[0]) < 0.1 * imW and abs(
                                    (ymin + ymax) / 2 - prev_center[1]) < 0.1 * imH:
                                matched_id = obj_id
                                break

                    if matched_id is None:
                        # Verificar si el objeto actual coincide con algún objeto fantasma
                        for ghost_id, ghost_data in ghost_objects.items():
                            if object_name == ghost_data['name']:
                                prev_center = ghost_data['center']
                                if abs((xmin + xmax) / 2 - prev_center[0]) < 0.1 * imW and abs(
                                        (ymin + ymax) / 2 - prev_center[1]) < 0.1 * imH:
                                    matched_id = ghost_id
                                    del ghost_objects[ghost_id]
                                    break

                    if matched_id is None:
                        matched_id = object_id
                        object_id += 1

                    new_tracked_objects[matched_id] = {'name': object_name,
                                                       'center': ((xmin + xmax) / 2, (ymin + ymax) / 2)}

                    # Actualizar historial de colores
                    if matched_id in color_history:
                        prev_color = color_history[matched_id]
                    else:
                        prev_color = None

                    if internal_color == (0, 0, 255) and prev_color == (
                    10, 255, 0) and matched_id not in detected_object_ids:
                        frame_time = frame_count / fps
                        start_event_time = frame_time - 2
                        end_event_time = frame_time + 1 + random.uniform(0, 1)
                        event_list.append({
                            'start_time': time.strftime("%H:%M:%S", time.gmtime(start_event_time)),
                            'end_time': time.strftime("%H:%M:%S", time.gmtime(end_event_time))
                        })
                        detected_object_ids.add(matched_id)
                        print(f"Id del objeto: {matched_id}, Clase: {object_name}, Posición: {((xmin + xmax) / 2, (ymin + ymax) / 2)}")

                    color_history[matched_id] = internal_color

                    label = '%s: %d%% ID:%d' % (object_name, int(scores[i] * 100), matched_id)
                    cv2.putText(frame, label, (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                    detections.append([object_name, scores[i], xmin, ymin, xmax, ymax, matched_id])

                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color, 2)
                    label = '%s: %d%%' % (object_name, int(scores[i] * 100))
                    labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                    label_ymin = max(ymin, labelSize[1] + 10)
                    cv2.rectangle(frame, (xmin, label_ymin - labelSize[1] - 10),
                                  (xmin + labelSize[0], label_ymin + baseLine - 10), (255, 255, 255),
                                  cv2.FILLED)
                    cv2.putText(frame, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

            frame_to_write = True


            for obj_id, obj_data in tracked_objects.items():
                if obj_id not in new_tracked_objects:
                    ghost_objects[obj_id] = {'name': obj_data['name'], 'center': obj_data['center'],
                                             'frames': frame_count}

            tracked_objects = new_tracked_objects

            if frame_to_write:
                out.write(frame)  # Solo escribir el frame si se ha procesado
                cv2.imshow('output', frame)  # Solo mostrar el frame si se ha procesado

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        frame_count += 1
    cap.release()
    out.release()
    cv2.destroyAllWindows()
