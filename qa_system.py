import sqlite3
import tkinter as tk
from tkinter import scrolledtext, messagebox
import math

try:
    import seed_data
except ImportError:
    import sys
    sys.path.insert(0, '.')
    import seed_data


class KnowledgeBase:
    def __init__(self, db_path='knowledge_base.db'):
        self.db_path = db_path
        self.qa_dict = {}
        self.keyword_set = set()
        self.keyword_category_map = {}
        self.question_keywords_map = {}
        self.keyword_weights = {}

        seed_data.ensure_initialized()
        self._load_data()

    def _load_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM questions')
        count = cursor.fetchone()[0]
        if count == 0:
            print("警告：数据库中没有数据！")
            conn.close()
            return

        self.keyword_priority_map = {}

        cursor.execute('SELECT id, question, answer FROM questions')
        for qid, question, answer in cursor.fetchall():
            self.qa_dict[question] = answer

            cursor.execute('SELECT keyword, weight, priority FROM question_keywords WHERE question_id = ?', (qid,))
            kw_data = cursor.fetchall()
            keywords = [row[0] for row in kw_data]
            weights = {row[0]: row[1] for row in kw_data}
            self.question_keywords_map[question] = {'keywords': set(keywords), 'weights': weights}

            for keyword, weight, priority in kw_data:
                self.keyword_set.add(keyword)
                self.keyword_weights[keyword] = weight
                self.keyword_priority_map[keyword] = priority
                if keyword not in self.keyword_category_map:
                    self.keyword_category_map[keyword] = []
                self.keyword_category_map[keyword].append(question)

        self._compute_idf_weights(count)

        conn.close()

    def _compute_idf_weights(self, total_questions):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT keyword, COUNT(DISTINCT question_id) as df FROM question_keywords GROUP BY keyword')
        df_data = cursor.fetchall()

        idf_values = []
        for keyword, df in df_data:
            if df > 0:
                idf = math.log(total_questions / df)
                idf_values.append(idf)

        if idf_values:
            max_idf = max(idf_values)
            min_idf = min(idf_values)
            idf_range = max_idf - min_idf
        else:
            max_idf = min_idf = idf_range = 0

        for keyword, df in df_data:
            if df > 0 and idf_range > 0:
                idf = math.log(total_questions / df)
                normalized_idf = (idf - min_idf) / idf_range
            else:
                normalized_idf = 0

            priority = self.keyword_priority_map.get(keyword, 1)

            new_weight = 1.0 + normalized_idf * 10.0 + priority * 2.0

            self.keyword_weights[keyword] = new_weight
            cursor.execute('UPDATE question_keywords SET weight = ? WHERE keyword = ?', (new_weight, keyword))

        for question, data in self.question_keywords_map.items():
            updated_weights = {kw: self.keyword_weights.get(kw, 1.0) for kw in data['keywords']}
            data['weights'] = updated_weights

        conn.commit()
        conn.close()

    def extract_keywords(self, text):
        text = text.strip()
        if not text:
            return {}

        keywords = {}
        sorted_keywords = sorted(self.keyword_set, key=lambda x: -len(x))

        temp_text = text
        matched_positions = []

        for kw in sorted_keywords:
            if len(kw) <= len(temp_text):
                idx = temp_text.find(kw)
                if idx != -1:
                    keywords[kw] = self.keyword_weights.get(kw, 1.0)
                    start_pos = idx
                    end_pos = idx + len(kw)
                    matched_positions.append((start_pos, end_pos))

        matched_text = [' '] * len(text)
        for start, end in matched_positions:
            for i in range(start, end):
                if i < len(matched_text):
                    matched_text[i] = '#'

        for kw in sorted_keywords:
            if kw in keywords:
                continue
            idx = text.find(kw)
            if idx != -1:
                is_overlap = False
                for start, end in matched_positions:
                    if not (idx + len(kw) <= start or idx >= end):
                        is_overlap = True
                        break
                if not is_overlap:
                    keywords[kw] = self.keyword_weights.get(kw, 1.0)

        return keywords

    def _detect_question_type(self, text):
        type_keywords = {
            'definition': ['什么是', '什么叫做', '定义', '概念', '含义', '意思'],
            'role': ['作用', '用途', '应用', '应用场景', '为什么用', '用来做什么'],
            'difference': ['区别', '差异', '不同', '对比', '比较'],
            'how': ['如何', '怎么', '怎样', '方法', '步骤'],
            'list': ['有哪些', '包括', '包含', '分类'],
            'advantage': ['优点', '优势', '好处'],
            'disadvantage': ['缺点', '劣势', '不足'],
            'principle': ['原理', '机制', '工作原理'],
        }
        
        detected_types = []
        for qtype, keywords in type_keywords.items():
            for kw in keywords:
                if kw in text:
                    detected_types.append(qtype)
                    break
        return detected_types

    def match_question(self, user_question):
        matched = self.match_top_questions(user_question, top_n=1)
        return matched[0][0] if matched else None

    def match_top_questions(self, user_question, top_n=3):
        if not user_question or user_question.strip() == "":
            return []

        user_keywords = self.extract_keywords(user_question)
        if not user_keywords:
            return []

        question_types = self._detect_question_type(user_question)

        candidates = []

        for question, data in self.question_keywords_map.items():
            question_keywords = data['keywords']
            question_weights = data['weights']

            intersection = user_keywords.keys() & question_keywords
            if not intersection:
                continue

            weighted_score = sum(user_keywords[kw] * question_weights.get(kw, 1.0) for kw in intersection)
            intersection_count = len(intersection)

            type_match_count = 0
            if question_types:
                for qtype in question_types:
                    if qtype == 'difference':
                        if '区别' in question or '差异' in question or '不同' in question:
                            type_match_count += 1
                    elif qtype == 'role':
                        if '作用' in question or '用途' in question or '应用' in question:
                            type_match_count += 1
                    elif qtype == 'definition':
                        if '什么是' in question or '定义' in question or '概念' in question:
                            type_match_count += 1

            if type_match_count > 0:
                weighted_score *= (1 + type_match_count * 0.5)

            if intersection_count >= 2:
                weighted_score *= (1 + (intersection_count - 1) * 0.3)

            candidates.append((question, weighted_score, intersection_count, type_match_count))

        candidates.sort(key=lambda x: (-x[1], -x[3], -x[2]))

        return candidates[:top_n]

    def get_answer(self, user_question):
        matched_question = self.match_question(user_question)
        if matched_question:
            return self.qa_dict[matched_question]
        return None

    def get_joint_answer(self, user_question, max_knowledge=5):
        top_matches = self.match_top_questions(user_question, top_n=max_knowledge)
        if not top_matches:
            return None

        answers = []
        used_keywords = set()

        for question, score, intersection_count, type_match_count in top_matches:
            question_keywords = self.question_keywords_map[question]['keywords']
            new_keywords = question_keywords - used_keywords

            if new_keywords or len(answers) == 0:
                answer = self.qa_dict[question]
                answers.append({
                    'question': question,
                    'answer': answer,
                    'score': score,
                    'keywords': new_keywords,
                    'type_match': type_match_count
                })
                used_keywords.update(question_keywords)

        if len(answers) == 1:
            return answers[0]['answer']

        combined = "根据多条知识，为您综合分析如下：\n\n"
        for i, item in enumerate(answers, 1):
            combined += f"{i}. {item['question']}\n"
            combined += f"   {item['answer']}\n\n"

        combined += "以上内容综合了多个相关知识点，希望能帮助您全面理解该问题。"
        return combined


class QAGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("人工智能基础问答系统")
        self.master.geometry("700x500")

        self.knowledge_base = KnowledgeBase()
        self.query_history = []

        self._create_widgets()

    def _create_widgets(self):
        self.chat_display = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=80, height=20)
        self.chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.chat_display.insert(tk.END, "欢迎使用人工智能基础问答系统！\n请输入您的问题，输入'退出'结束对话。\n勾选'联合分析'可综合多条知识回答复杂问题。\n\n")
        self.chat_display.config(state=tk.DISABLED)

        self.input_frame = tk.Frame(self.master)
        self.input_frame.pack(padx=10, pady=5, fill=tk.X)

        self.input_entry = tk.Entry(self.input_frame, width=60)
        self.input_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.input_entry.bind("<Return>", self.handle_send)

        self.joint_var = tk.BooleanVar()
        self.joint_checkbox = tk.Checkbutton(self.input_frame, text="联合分析", variable=self.joint_var)
        self.joint_checkbox.pack(side=tk.LEFT, padx=5)

        self.send_button = tk.Button(self.input_frame, text="发送", command=self.handle_send)
        self.send_button.pack(side=tk.LEFT, padx=5)

        self.exit_button = tk.Button(self.input_frame, text="退出", command=self.master.quit)
        self.exit_button.pack(side=tk.LEFT, padx=5)

    def handle_send(self, event=None):
        user_input = self.input_entry.get().strip()
        if not user_input:
            return

        self.input_entry.delete(0, tk.END)

        if user_input == "退出":
            self.master.quit()
            return

        self.query_history.append(user_input)

        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"您: {user_input}\n")
        self.chat_display.config(state=tk.DISABLED)

        if self.joint_var.get():
            answer = self.knowledge_base.get_joint_answer(user_input)
            prefix = "系统（联合分析）:"
        else:
            answer = self.knowledge_base.get_answer(user_input)
            prefix = "系统:"

        if answer:
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, f"{prefix} {answer}\n\n")
            self.chat_display.config(state=tk.DISABLED)
        else:
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, "系统: 抱歉，未找到相关答案，请尝试其他问题\n\n")
            self.chat_display.config(state=tk.DISABLED)

        self.chat_display.see(tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = QAGUI(root)
    root.mainloop()
