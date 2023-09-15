from django.test import TestCase
from django.conf import settings
import openpyxl
from typing import List
from results.models import SemesterEnroll, Semester
import unittest
from termcolor import colored
# Create your tests here.

def get_excel_dataset(header: List, data_rows:List, credits_idxs:List, gp_idxs: List):
    dataset = {}
    reg_idx = header.index('reg')
    for row in data_rows:
        registration = int(row[reg_idx].value)
        dataset[registration] = {}
        for credit_i in credits_idxs:
            credit_header = header[credit_i]
            semester_number = int(credit_header.split('-')[-1])
            semester_credits = row[credit_i].value
            dataset[registration][semester_number] = {
                'credits': semester_credits
            }
        for gp_i in gp_idxs:
            gp_header = header[gp_i]
            semester_number = int(gp_header.split('-')[-1])
            semester_gp = row[gp_i].value
            dataset[registration][semester_number]['gp'] = semester_gp
            if semester_number in dataset[registration].keys():
                dataset[registration][semester_number]['gp'] = semester_gp
                
    return dataset
        


class SemesterResultsTestCase(TestCase):
    fixtures = [settings.BASE_DIR/'fixtures.json']
    
    def test_semester_results(self):
        # data preparation
        excel_file = settings.BASE_DIR/"anunad_results.xlsx"
        wb = openpyxl.load_workbook(excel_file)
        sheet1 = wb[wb.sheetnames[0]]
        rows = list(sheet1.rows)
        header = [cell.value.lower().strip() for cell in rows[0] if cell.value is not None]
        data_rows = rows[1:]
        credits_idxs = [header.index(col) for col in header if col.startswith("credit")]
        gp_idxs = [header.index(col) for col in header if col.startswith("gp")]
        self.assertEqual(len(credits_idxs), len(gp_idxs))
        dataset = get_excel_dataset(header, data_rows, credits_idxs, gp_idxs)
        # model preparation
        semesters = Semester.objects.filter(session__from_year=2018)
        for sem in semesters:
            success = 0
            print(f"# Running test for semester: {sem}")
            semester_enrollments = sem.semesterenroll_set.all()
            for enroll in semester_enrollments:
                reg = enroll.student.registration
                try:
                    actual_credits = dataset[reg][sem.semester_no]['credits']
                    actual_gp = dataset[reg][sem.semester_no]['gp']
                except Exception as exe:
                    continue
                messsage = f"{reg} <-- {sem}"
                try:
                    self.assertEqual(enroll.semester_credits, actual_credits, msg=messsage)
                except AssertionError:
                    print(colored(f"Mismatch Credits --> Reg: {reg} , db: {enroll.semester_credits} , actual {actual_credits}", 'light_red'))
                try:
                    self.assertEqual(enroll.semester_gpa, actual_gp, msg=messsage)
                except AssertionError:
                    # print(f"Mismatch GP --> Reg: {reg} , db: {enroll.semester_gpa} , actual {actual_gp}")
                    print(colored(f"Mismatch GP --> Reg: {reg} , db: {enroll.semester_gpa} , actual {actual_gp}", "red"))
                    continue
                success += 1
            print(colored(f"successful: {success} / {semester_enrollments.count()}", 'light_green'))
        
        
        
        
