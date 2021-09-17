#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('FHIR_Translator_API/swagger')
def generate_swagger():
        return render_template('index.html')

@app.route('/generateR4Patient/', methods=['POST'])
def generator_r4patient():
    patients = request.get_json(force = True)
    gender_mapper = {
        'm': 'male',
        'f': 'female',
        'o': 'other',
        'u': 'unknown',
        }
    custom_json = []
    for patient in patients:
        data = {
            'resourceType': 'Patient',
            'id': str(patient['uuid']),
            'identifier': [{
                'use': 'usual',
                'type': {'coding': [{'system': 'http://terminology.hl7.org/CodeSystem/v2-0203', 'code': 'MR'}]},
                'system': 'urn:oid:1.2.36.146.595.217.0.1',
                'value': str(patient['id']),
                }],
            'active': True,
            'name': [{'use': 'official',
                     'family': str(patient['patientsname']),
                     'given': [str(patient['patientsname'])]}],
            'gender': (gender_mapper[str(patient['patientssex'
                       ]).lower()] if patient.get('patientssex') else ''
                       ),
            'birthDate': ((patient['patientsbirthdate'])[0:4] + '-'
                          + (patient['patientsbirthdate'])[4:6] + '-'
                          + (patient['patientsbirthdate'
                          ])[6:8] if patient.get('patientsbirthdate',
                          None) else ''),
            'extension': [{'url': 'https://citiustech/imagingstudy/patient_extension/patient_creatorid'
                          , 'valueString': str(patient['creatorid'])},
                          {'url': 'https://citiustech/imagingstudy/patient_extension/patient_projectid'
                          , 'valueString': str(patient['projectid'])}],
            }

        customs_json = json.dumps(data)
        custom_json.append(customs_json)
        final_json = str(custom_json)
        final_json = final_json.replace("'{","{")
        final_json = final_json.replace("}'", "}")
     #   custom_json +=  str(customs_json)
     #       custom_json.append(str(custom_json) + "," + str(customs_json))

    return final_json

@app.route('/generateR4ImagingStudy/', methods=['POST'])
def generator_r4imagingstudy():
    study_list = request.get_json(force=True)

    def get_series(series_list):
        res = []
        for series_data in series_list:
            data = {
                "uid": str(series_data["seriesinstanceuid"]),
                "number": series_data["seriesnumber"],
                "modality": {
                    "system": "http://dicom.nema.org/resources/ontology/DCM",
                    "code": str(series_data["modality"])
                },
                "description": str(series_data["seriesdescription"]),
                "started": series_data["seriesdatetime"][0:10] + "T" + series_data["seriesdatetime"][
                                                                       11:19] + "Z" if series_data.get("seriesdatetime",
                                                                                                       None) else "",
                "extension": [{
                    "url": "https://citiustech/imagingstudy/series_extension/seriesid",
                    "valueString": str(series_data["id"])
                },
                    {
                        "url": "https://citiustech/imagingstudy/series_extension/studyid",
                        "valueString": str(series_data["studyid"])
                    },
                    {
                        "url": "https://citiustech/imagingstudy/series_extension/manufacturersmodelname",
                        "valueString": str(series_data["manufacturersmodelname"])
                    },
                    {
                        "url": "https://citiustech/imagingstudy/series_extension/archived",
                        "valueString": str(series_data["archived"])
                    }

                ]
            }
            if series_data.get("instance"):
                data["instance"] = series_data["instance"]
            res.append(data)
        return res

    study_custom_json = []
    for study in study_list:
        series = get_series(study["series"])
        study_data = {
            "resourceType": "ImagingStudy",
            "id": str(study["uuid"]),
            "identifier": [
                {
                    "value": str(study["id"])
                },
                {
                    "value": str(study["studyinstanceuid"])
                },
                {
                    "use": "usual",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "ACSN"
                            }
                        ]
                    },
                    "value": str(study["accessionnumber"]),
                }
            ],
            "status": "available",
            "modality": [
                {
                    "system": "http://dicom.nema.org/resources/ontology/DCM",
                    "code": study["series"][0]["modality"] if study.get("series", None) else ""
                }
            ],
            "subject": {
                "reference": "Patient/" + str(study["patient_uuid"]),
                "type": "Patient"
            },
            "started": study["studydatetime"][0:10] + "T" + study["studydatetime"][11:19] + "Z" if study.get(
                "studydatetime", None) else "",
            "numberOfSeries": len(series),
            "description": str(study["studydescription"]),
            "series": series,
            "extension": [
                {
                    "url": "https://citiustech/imagingstudy/study_extension/studyid",
                    "valueString": str(study["studyid"]) if study.get("studyid", None) else "NA"
                },
                {
                    "url": "https://citiustech/imagingstudy/study_extension/creatorid",
                    "valueString": str(study["creatorid"])
                },
                {
                    "url": "https://citiustech/imagingstudy/study_extension/scan_id",
                    "valueString": str(study["scan_id"])
                }
            ]
        }

        study_customs_json = json.dumps(study_data)
        study_custom_json.append(study_customs_json)
        final_study_json = str(study_custom_json)
        final_study_json = final_study_json.replace("'{", "{")
        final_study_json = final_study_json.replace("}'", "}")

        return final_study_json

if __name__ == '__main__':
    app.run(debug=True, port=9999)
