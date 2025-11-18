import os
import psycopg2

class DatabaseService:
    def __init__(self, host: str, port: int, user: str, database: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = os.environ.get("local_postgres_password", "")
        self.database = database

    def start_connection(self):
        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.conn = conn
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            return None
        
    def close_connection(self):
        if self.conn:
            self.conn.close()
        
    def insert_resume(self, resume_data: dict):
        try:
            cursor = self.conn.cursor()
            insert_query = """
                INSERT INTO resumescreener.resumes (name, email, phone, summary)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """
            cursor.execute(insert_query, (
                resume_data.get("name"),
                resume_data.get("email"),
                resume_data.get("phone"),
                resume_data.get("summary"),
            ))
            resume_id = cursor.fetchone()[0]
            self.conn.commit()
            cursor.close()
            return resume_id
        except psycopg2.Error as e:
            print(f"Error inserting resume data: {e}")
            self.conn.rollback()

    def insert_skills(self, resume_id: int, skills: list):
        try:
            cursor = self.conn.cursor()
            insert_query = """
                INSERT INTO resumescreener.skills (resume_id, skill)
                VALUES (%s, %s);
            """
            for skill in skills:
                cursor.execute(insert_query, (resume_id, skill))
            self.conn.commit()
            cursor.close()
        except psycopg2.Error as e:
            print(f"Error inserting skills: {e}")
            self.conn.rollback()

    def insert_experience(self, resume_id: int, experience_list: list):
        try:
            cursor = self.conn.cursor()
            insert_query = """
                INSERT INTO resumescreener.experience (resume_id, company, role, start_date, end_date, description)
                VALUES (%s, %s, %s, %s, %s, %s);
            """
            for exp in experience_list:
                cursor.execute(insert_query, (
                    resume_id,
                    exp.get("company"),
                    exp.get("role"),
                    exp.get("start_date"),
                    exp.get("end_date"),
                    exp.get("description"),
                ))
            self.conn.commit()
            cursor.close()
        except psycopg2.Error as e:
            print(f"Error inserting experience: {e}")
            self.conn.rollback()

    def insert_education(self, resume_id: int, education_list: list):
        try:
            cursor = self.conn.cursor()
            insert_query = """
                INSERT INTO resumescreener.education (resume_id, institution, degree, start_year, end_year)
                VALUES (%s, %s, %s, %s, %s);
            """
            for edu in education_list:
                cursor.execute(insert_query, (
                    resume_id,
                    edu.get("institution"),
                    edu.get("degree"),
                    edu.get("start_year"),
                    edu.get("end_year"),
                ))
            self.conn.commit()
            cursor.close()
        except psycopg2.Error as e:
            print(f"Error inserting education: {e}")
            self.conn.rollback()

    def get_resume_by_id(self, resume_id: int):
        try:
            cursor = self.conn.cursor()
            select_query = """
                SELECT id, name, email, phone, summary
                FROM resumescreener.resumes
                WHERE id = %s;
            """
            cursor.execute(select_query, (resume_id,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                return {
                    "id": result[0],
                    "name": result[1],
                    "email": result[2],
                    "phone": result[3],
                    "summary": result[4],
                }
            return None
        except psycopg2.Error as e:
            print(f"Error retrieving resume: {e}")
            return None
        
    def get_skills_by_resume_id(self, resume_id: int):
        try:
            cursor = self.conn.cursor()
            select_query = """
                SELECT skill
                FROM resumescreener.skills
                WHERE resume_id = %s;
            """
            cursor.execute(select_query, (resume_id,))
            results = cursor.fetchall()
            cursor.close()
            return [row[0] for row in results]
        except psycopg2.Error as e:
            print(f"Error retrieving skills: {e}")
            return []
    
    def get_experience_by_resume_id(self, resume_id: int):
        try:
            cursor = self.conn.cursor()
            select_query = """
                SELECT company, role, start_date, end_date, description
                FROM resumescreener.experience
                WHERE resume_id = %s;
            """
            cursor.execute(select_query, (resume_id,))
            results = cursor.fetchall()
            cursor.close()
            experience_list = []
            for row in results:
                experience_list.append({
                    "company": row[0],
                    "role": row[1],
                    "start_date": row[2],
                    "end_date": row[3],
                    "description": row[4],
                })
            return experience_list
        except psycopg2.Error as e:
            print(f"Error retrieving experience: {e}")
            return []
    
    def get_education_by_resume_id(self, resume_id: int):
        try:
            cursor = self.conn.cursor()
            select_query = """
                SELECT institution, degree, start_year, end_year
                FROM resumescreener.education
                WHERE resume_id = %s;
            """
            cursor.execute(select_query, (resume_id,))
            results = cursor.fetchall()
            cursor.close()
            education_list = []
            for row in results:
                education_list.append({
                    "institution": row[0],
                    "degree": row[1],
                    "start_year": row[2],
                    "end_year": row[3],
                })
            return education_list
        except psycopg2.Error as e:
            print(f"Error retrieving education: {e}")
            return []