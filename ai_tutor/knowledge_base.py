"""
Local Educational Knowledge Base for SmartEdu Demo AI Tutor.

Contains curated, deterministic educational knowledge across 10 core computer science
and edtech topics. Structured for clean keyword matching, explanation, key points,
revision questions, and study strategies without external API dependencies.
"""

KNOWLEDGE_BASE = {
    # --------------------------------------------------------------------------
    # 1. PYTHON PROGRAMMING
    # --------------------------------------------------------------------------
    "python_basics": {
        "topic_name": "Python Fundamentals",
        "category": "Programming Languages",
        "keywords": [
            "python", "python programming", "python syntax", "python variables",
            "python data types", "lists in python", "dictionaries in python",
            "python functions", "list comprehension", "generators", "decorators"
        ],
        "explanation": (
            "Python is a high-level, interpreted, general-purpose programming language known for its clear, "
            "readable syntax and dynamic typing. It supports multiple programming paradigms, including procedural, "
            "object-oriented, and functional styles. Key built-in data structures include Lists (ordered, mutable), "
            "Tuples (ordered, immutable), Sets (unordered, unique elements), and Dictionaries (key-value mappings). "
            "Advanced Python features include list comprehensions for concise transformations, generators for memory-efficient "
            "iteration using the 'yield' keyword, and decorators for modifying function behavior using the '@' syntax."
        ),
        "key_points": [
            "Interpreted & Dynamically Typed: Code is executed line-by-line without an explicit ahead-of-time compilation step.",
            "Indentation Matters: Python uses whitespace indentation instead of curly braces to define code blocks.",
            "Core Data Structures: Lists (mutable sequences), Tuples (immutable sequences), Sets (unique elements), Dictionaries (hash tables).",
            "Memory Management: Automatic garbage collection utilizing reference counting and a cyclic garbage collector.",
            "Batteries Included: Comprehensive standard library covering math, regular expressions, file I/O, networking, and JSON."
        ],
        "revision_questions": [
            {
                "question": "What is the key difference between a Python List and a Tuple?",
                "answer": "Lists are mutable (can be changed after creation using append, remove, etc.), whereas Tuples are immutable and consume less memory."
            },
            {
                "question": "How does a generator differ from a standard Python function?",
                "answer": "A standard function returns a single value via 'return' and terminates. A generator uses 'yield' to produce a lazy sequence of values on demand without storing the entire sequence in memory."
            },
            {
                "question": "What is a Python decorator and how is it applied?",
                "answer": "A decorator is a callable that takes a function as an argument and extends its behavior without modifying the original code. It is applied using the '@decorator_name' syntax."
            }
        ],
        "study_strategies": [
            "Implement small utility scripts to reinforce list comprehensions and dictionary operations.",
            "Practice writing unit tests with unittest or pytest to build confidence with edge cases.",
            "Use virtual environments (venv) for every project to avoid dependency conflicts."
        ],
        "suggested_next_topics": ["oop_principles", "django_fundamentals", "data_structures"]
    },

    # --------------------------------------------------------------------------
    # 2. HTML, CSS, AND JAVASCRIPT
    # --------------------------------------------------------------------------
    "web_frontends": {
        "topic_name": "HTML, CSS, and Modern JavaScript",
        "category": "Web Development",
        "keywords": [
            "html", "css", "javascript", "dom", "flexbox", "css grid", "responsive design",
            "async await", "promises", "event loop", "fetch api", "es6", "vanilla js"
        ],
        "explanation": (
            "Web frontend development is built upon the triad of HTML, CSS, and JavaScript. "
            "HTML (HyperText Markup Language) provides the semantic skeleton and document hierarchy. "
            "CSS (Cascading Style Sheets) controls presentation, styling, typography, and responsive layouts through modern layout engines like Flexbox (1-dimensional) and CSS Grid (2-dimensional). "
            "JavaScript provides client-side reactivity, asynchronous network communication via the Fetch API and Promises, and DOM manipulation. JavaScript operates on a single-threaded Event Loop featuring a Call Stack, Web APIs, Microtask Queue, and Callback Queue."
        ),
        "key_points": [
            "Semantic HTML: Using tags like <nav>, <article>, <header>, <section> enhances accessibility and search engine optimization.",
            "Box Model: Elements consist of Content, Padding, Border, and Margin. 'box-sizing: border-box' simplifies sizing calculations.",
            "Layout Engines: Flexbox is optimized for directional flow (row/column); CSS Grid excels at two-dimensional grid systems.",
            "JavaScript Event Loop: Non-blocking asynchronous behavior relies on promises, microtask queues, and the macrotask loop.",
            "Async/Await: Syntactic sugar built on top of Promises for writing readable asynchronous code."
        ],
        "revision_questions": [
            {
                "question": "What is the CSS Box Model and how does 'box-sizing: border-box' alter it?",
                "answer": "The box model includes Content, Padding, Border, and Margin. With 'border-box', padding and border are included in the element's specified width/height rather than expanding it."
            },
            {
                "question": "Explain how the JavaScript Event Loop handles asynchronous callbacks.",
                "answer": "Synchronous code runs on the Call Stack. Asynchronous tasks (like fetch or timers) are delegated to browser APIs; when ready, their callbacks wait in queues (Microtask for Promises, Macrotask for setTimeout) and run once the stack is empty."
            },
            {
                "question": "Why should developers use semantic HTML elements instead of generic <div> tags?",
                "answer": "Semantic tags provide meaningful structure for assistive screen readers, search engine indexing, and maintainable styling."
            }
        ],
        "study_strategies": [
            "Build complete UI components (e.g. modals, responsive navbars, tabs) using pure CSS and Vanilla JS before reaching for frameworks.",
            "Inspect web pages using Chrome DevTools to debug layout shifts, box model metrics, and network requests.",
            "Practice consuming public REST APIs using fetch and async/await with robust error handling."
        ],
        "suggested_next_topics": ["django_fundamentals", "python_basics"]
    },

    # --------------------------------------------------------------------------
    # 3. DJANGO FUNDAMENTALS
    # --------------------------------------------------------------------------
    "django_fundamentals": {
        "topic_name": "Django Web Framework",
        "category": "Backend Engineering",
        "keywords": [
            "django", "django mvt", "django orm", "django migrations", "django views",
            "django models", "django templates", "django forms", "django urls",
            "django middleware", "django authentication"
        ],
        "explanation": (
            "Django is a high-level, batteries-included Python web framework designed for rapid development and clean design. "
            "It follows the Model-View-Template (MVT) architecture: Models define database structure and business logic using Django's ORM; "
            "Views handle HTTP requests and orchestrate data; Templates render HTML to the client. "
            "Django features an automated migration system, built-in CSRF/XSS security protections, role-based authentication, "
            "and an extensible admin interface. Middleware acts as a hook mechanism during request and response processing."
        ),
        "key_points": [
            "MVT Pattern: Model (Data layer via ORM), View (Business logic & request routing), Template (Presentation layer).",
            "Django ORM: Maps Python classes to relational database tables, supporting lazy query evaluation and aggregation.",
            "Migrations: Automated system (`makemigrations`, `migrate`) tracking model changes in version-controlled migration files.",
            "Built-in Security: Automatic CSRF token validation, SQL injection prevention via parameterized queries, clickjacking protection.",
            "Authentication: Comprehensive user management with session cookies, permission flags, and extensible custom user models."
        ],
        "revision_questions": [
            {
                "question": "How does Django's MVT architecture compare to the traditional MVC pattern?",
                "answer": "In Django MVT, the Model is the database layer, the View handles controller logic, and the Template is the visual view. Django itself acts as the controller routing requests."
            },
            {
                "question": "Why are Django QuerySets described as 'lazy'?",
                "answer": "QuerySets do not hit the database when created; evaluation happens only when iterated over, sliced, evaluated in an if statement, or converted to a list."
            },
            {
                "question": "What is the purpose of Django CSRF tokens in HTML forms?",
                "answer": "Cross-Site Request Forgery (CSRF) tokens ensure that POST/PUT/DELETE requests originate from an authenticated user on your own site, rather than a malicious external domain."
            }
        ],
        "study_strategies": [
            "Always inspect raw queries using connection.queries or django-debug-toolbar to detect N+1 query bottlenecks.",
            "Practice writing Custom User Models from the start of every Django project using AbstractUser.",
            "Organize complex business logic into reusable service layers rather than over-stuffing views or models."
        ],
        "suggested_next_topics": ["sql_databases", "dbms_normalization", "python_basics"]
    },

    # --------------------------------------------------------------------------
    # 4. SQL AND DATABASE MANAGEMENT
    # --------------------------------------------------------------------------
    "sql_databases": {
        "topic_name": "SQL & Relational Database Management",
        "category": "Databases & Storage",
        "keywords": [
            "sql", "databases", "relational database", "rdbms", "crud", "joins",
            "inner join", "left join", "right join", "indexing", "b-tree",
            "transactions", "acid properties", "foreign keys", "primary key"
        ],
        "explanation": (
            "Relational Database Management Systems (RDBMS) like PostgreSQL, MySQL, and SQLite store structured data in tables composed of rows and columns. "
            "Structured Query Language (SQL) is the standard declarative language for querying and manipulating data. "
            "SQL operations encompass DDL (Data Definition Language), DML (Data Manipulation Language), and DQL (Data Query Language). "
            "Table relationships are established through Primary Keys and Foreign Keys. Database transactions adhere to ACID properties "
            "(Atomicity, Consistency, Isolation, Durability) to ensure data reliability during concurrent operations."
        ),
        "key_points": [
            "ACID Properties: Atomicity (all-or-nothing), Consistency (rules enforced), Isolation (concurrent safety), Durability (persisted changes).",
            "SQL Joins: INNER JOIN (matching rows in both tables), LEFT JOIN (all left rows + matching right rows), FULL OUTER JOIN (all rows from both).",
            "Indexes: Data structures (predominantly B-Trees) that dramatically speed up data retrieval at the cost of slower writes and additional disk space.",
            "Constraints: Primary Key, Unique, Foreign Key, Check, and Not Null enforce domain and referential integrity.",
            "Query Optimization: Using EXPLAIN to analyze query execution plans and index usage."
        ],
        "revision_questions": [
            {
                "question": "What are ACID properties in database transaction management?",
                "answer": "Atomicity (all operations succeed or rollback), Consistency (valid state transitions), Isolation (independent concurrent execution), and Durability (committed data survives crashes)."
            },
            {
                "question": "Differentiate between an INNER JOIN and a LEFT JOIN in SQL.",
                "answer": "INNER JOIN returns only rows with matching values in both tables; LEFT JOIN returns all rows from the left table alongside matched rows from the right table (with NULL for non-matches)."
            },
            {
                "question": "Why do indexes speed up SELECT queries but slow down INSERT/UPDATE statements?",
                "answer": "Indexes allow fast binary/B-Tree searching for reads, but every write operation requires updating both the base table and the associated index tree."
            }
        ],
        "study_strategies": [
            "Write SQL queries by hand before using ORM wrappers to understand how JOINs and GROUP BY filters operate.",
            "Use SQLite via the CLI or PostgreSQL with pgAdmin to experiment with EXPLAIN QUERY PLAN.",
            "Design Entity-Relationship (ER) diagrams before building database schemas."
        ],
        "suggested_next_topics": ["dbms_normalization", "django_fundamentals", "data_structures"]
    },

    # --------------------------------------------------------------------------
    # 5. DBMS NORMALIZATION AND INDEXING
    # --------------------------------------------------------------------------
    "dbms_normalization": {
        "topic_name": "DBMS Normalization & Indexing Techniques",
        "category": "Databases & Storage",
        "keywords": [
            "dbms normalization", "database normalization", "normalization", "dbms",
            "1nf", "2nf", "3nf", "bcnf", "boyce codd", "functional dependency",
            "database anomalies", "insertion anomaly", "deletion anomaly", "update anomaly",
            "b-tree index", "hash index", "composite index"
        ],
        "explanation": (
            "Normalization is a systematic technique for organizing database tables to minimize data redundancy and eliminate update, insertion, and deletion anomalies. "
            "It decomposes larger tables into smaller, well-structured tables linked by foreign keys. "
            "Normal forms build upon one another: 1NF requires atomic values; 2NF eliminates partial functional dependencies; "
            "3NF eliminates transitive dependencies; BCNF (Boyce-Codd Normal Form) is a stricter version where every determinant must be a candidate key. "
            "Indexing complements normalization by facilitating fast lookups through balanced search trees (B-Trees) and composite indexes."
        ),
        "key_points": [
            "1NF (First Normal Form): Every column contains atomic (indivisible) values, and each record is unique.",
            "2NF (Second Normal Form): Must be in 1NF and contain no partial dependencies (non-key attributes must depend on the whole candidate key).",
            "3NF (Third Normal Form): Must be in 2NF and contain no transitive dependencies (non-key attributes must not depend on other non-key attributes).",
            "BCNF: Every functional dependency X -> Y requires X to be a super key.",
            "Trade-offs: Over-normalization can lead to excessive JOIN overhead, which is why denormalization is sometimes used in analytics and data warehousing."
        ],
        "revision_questions": [
            {
                "question": "What is a transitive dependency in relational database design?",
                "answer": "A transitive dependency occurs when non-key attribute A determines non-key attribute B, which in turn determines non-key attribute C (A -> B -> C), violating 3NF."
            },
            {
                "question": "Describe the three database modification anomalies that normalization solves.",
                "answer": "Insertion Anomaly (inability to record facts without unrelated data), Deletion Anomaly (unintended loss of valid data when deleting a record), and Update Anomaly (inconsistent duplicates when updating values)."
            },
            {
                "question": "When might a database architect intentionally denormalize a schema?",
                "answer": "Denormalization is used in read-heavy applications, data warehouses, or reporting systems to reduce expensive multi-table JOINs and boost read throughput."
            }
        ],
        "study_strategies": [
            "Take un-normalized real-world tables (like invoice spreadsheets) and step-by-step convert them through 1NF, 2NF, and 3NF.",
            "Write down functional dependencies mathematically (X -> Y) to verify candidate keys.",
            "Analyze table relationships to choose appropriate single-column or composite indexes."
        ],
        "suggested_next_topics": ["sql_databases", "operating_systems", "data_structures"]
    },

    # --------------------------------------------------------------------------
    # 6. OPERATING SYSTEMS
    # --------------------------------------------------------------------------
    "operating_systems": {
        "topic_name": "Operating Systems & Concurrency",
        "category": "Computer Systems",
        "keywords": [
            "operating systems", "os", "process", "thread", "concurrency", "cpu scheduling",
            "fcfs", "round robin", "shortest job first", "deadlock", "banker's algorithm",
            "virtual memory", "paging", "segmentation", "system calls", "mutex", "semaphore"
        ],
        "explanation": (
            "An Operating System (OS) is system software that manages computer hardware, system resources, and provides common services for application programs. "
            "Key responsibilities include Process Management (creating, scheduling, and terminating execution contexts), "
            "Memory Management (virtual memory, page tables, demand paging to allow programs larger than physical RAM), "
            "File Systems, and I/O coordination. Concurrency primitives such as Mutexes and Semaphores synchronize access to shared memory. "
            "Deadlocks occur when processes enter a circular wait for resources under conditions of mutual exclusion, hold-and-wait, and no-preemption."
        ),
        "key_points": [
            "Process vs Thread: A process is an independent program in execution with its own memory space; a thread is a lightweight unit of execution within a process sharing the same address space.",
            "CPU Scheduling: Algorithms like FCFS (First-Come, First-Served), SJF (Shortest Job First), and Round Robin (time slicing) balance throughput and latency.",
            "Deadlock Conditions (Coffman Conditions): Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait.",
            "Virtual Memory: Abstract address spaces divided into fixed-size pages mapped to physical memory frames via Page Tables.",
            "Synchronization: Race conditions are prevented using locks, semaphores, and atomic operations to protect critical sections."
        ],
        "revision_questions": [
            {
                "question": "What is the primary difference between a process and a thread?",
                "answer": "A process has its own isolated address space and system resources; threads live inside a process, sharing code, data, and open files while maintaining their own registers and stack."
            },
            {
                "question": "What are the four necessary Coffman conditions for a deadlock to occur?",
                "answer": "1. Mutual Exclusion, 2. Hold and Wait, 3. No Preemption, and 4. Circular Wait."
            },
            {
                "question": "How does virtual memory solve the problem of physical memory constraints?",
                "answer": "It provides each program with a large contiguous virtual address space, loading only necessary pages into physical RAM frames (demand paging) and swapping inactive pages to disk."
            }
        ],
        "study_strategies": [
            "Simulate Round Robin and SJF scheduling algorithms on paper using Gantt charts.",
            "Write a multi-threaded program in Python or C to observe race conditions and resolve them using mutex locks.",
            "Study Linux command-line utilities like `top`, `ps`, and `free` to monitor processes and memory states."
        ],
        "suggested_next_topics": ["computer_networks", "data_structures", "oop_principles"]
    },

    # --------------------------------------------------------------------------
    # 7. COMPUTER NETWORKS
    # --------------------------------------------------------------------------
    "computer_networks": {
        "topic_name": "Computer Networks & Protocols",
        "category": "Computer Systems",
        "keywords": [
            "computer networks", "networking", "osi model", "tcp ip", "tcp vs udp",
            "ip address", "subnetting", "dns", "http", "https", "ssl tls", "routing",
            "three way handshake", "packet switching", "socket"
        ],
        "explanation": (
            "Computer networks allow computers and devices to exchange data across physical and wireless media using standardized communication protocols. "
            "The OSI 7-Layer Model (Physical, Data Link, Network, Transport, Session, Presentation, Application) provides a conceptual framework. "
            "The Internet operates on the pragmatic 4-Layer TCP/IP suite. At the transport layer, TCP provides reliable, connection-oriented data streaming "
            "with flow and congestion control (via a 3-way handshake), while UDP provides low-latency, connectionless transmission. "
            "Application protocols like HTTP/HTTPS, DNS, and SSH power modern web applications over TLS encryption."
        ),
        "key_points": [
            "OSI 7 Layers: Physical, Data Link (frames/MAC), Network (packets/IP), Transport (segments/TCP/UDP), Session, Presentation, Application (HTTP).",
            "TCP vs UDP: TCP guarantees delivery, ordering, and error-checking; UDP offers fast best-effort datagram delivery ideal for video streaming and gaming.",
            "TCP 3-Way Handshake: SYN -> SYN-ACK -> ACK establishes a synchronized, reliable connection.",
            "DNS (Domain Name System): Translates human-readable domain names (e.g. smartedu.local) into machine-routable IP addresses.",
            "HTTPS & TLS: HyperText Transfer Protocol Secure encrypts client-server communication using asymmetric public-key cryptography and symmetric session keys."
        ],
        "revision_questions": [
            {
                "question": "What happens during the TCP three-way handshake?",
                "answer": "1. Client sends SYN (synchronize). 2. Server responds with SYN-ACK. 3. Client responds with ACK (acknowledge). Both ends have established sequence numbers and connection state."
            },
            {
                "question": "Why is UDP preferred over TCP for live video streaming or gaming?",
                "answer": "UDP omits connection setup handshakes and retransmission delays, prioritizing speed and real-time delivery over complete packet reliability."
            },
            {
                "question": "What is the function of the Transport Layer in the OSI model?",
                "answer": "It provides end-to-end data delivery, flow control, segmentation, error detection, and port multiplexing between communicating processes."
            }
        ],
        "study_strategies": [
            "Use Wireshark or browser Network tabs to inspect actual TCP handshakes, TLS negotiations, and HTTP headers.",
            "Practice calculating IPv4 subnets and CIDR prefix masks (e.g., /24 vs /28).",
            "Trace network hops using `traceroute` or `ping` to understand routing hops across autonomous systems."
        ],
        "suggested_next_topics": ["operating_systems", "django_fundamentals", "web_frontends"]
    },

    # --------------------------------------------------------------------------
    # 8. DATA STRUCTURES AND ALGORITHMS
    # --------------------------------------------------------------------------
    "data_structures": {
        "topic_name": "Data Structures & Algorithms (DSA)",
        "category": "Computer Science Foundations",
        "keywords": [
            "data structures", "algorithms", "dsa", "arrays", "linked lists",
            "stacks", "queues", "binary search tree", "bst", "graphs", "bfs", "dfs",
            "sorting algorithms", "quicksort", "mergesort", "big o notation",
            "time complexity", "space complexity"
        ],
        "explanation": (
            "Data Structures organize and store data for efficient access and modification, while Algorithms are step-by-step procedures for solving computational problems. "
            "Linear data structures include Arrays (contiguous memory, O(1) random access), Linked Lists (nodes with pointers, O(1) insert/delete at head), "
            "Stacks (LIFO), and Queues (FIFO). Non-linear structures include Trees (Hierarchical; BSTs offer O(log n) average search) and Graphs (Nodes and Edges). "
            "Algorithm efficiency is evaluated through asymptotic Big O notation, measuring worst-case time and space growth as input size n expands. "
            "Divide-and-conquer sorting algorithms like MergeSort achieve guaranteed O(n log n) time."
        ),
        "key_points": [
            "Big O Notation: Expresses upper-bound scaling: O(1) constant, O(log n) logarithmic, O(n) linear, O(n log n) linearithmic, O(n^2) quadratic.",
            "Stacks & Queues: Stacks follow Last-In-First-Out (used in call stacks, undo buffers); Queues follow First-In-First-Out (used in message queues, BFS).",
            "Binary Search Tree (BST): Left subtree values < root < right subtree values. Offers O(log n) average search, but can degrade to O(n) if unbalanced.",
            "Graph Traversals: Breadth-First Search (BFS) uses a queue to explore level-by-level (shortest unweighted paths); Depth-First Search (DFS) uses recursion or a stack to explore deep paths.",
            "Sorting: MergeSort offers stable O(n log n) sorting with O(n) extra space; QuickSort offers in-place O(n log n) average performance."
        ],
        "revision_questions": [
            {
                "question": "What is the worst-case and average-case time complexity of QuickSort?",
                "answer": "Average-case is O(n log n) with balanced pivots; worst-case is O(n^2) when poor pivots (like already sorted arrays with naive pivot choice) lead to unbalanced partitions."
            },
            {
                "question": "How does Breadth-First Search (BFS) differ from Depth-First Search (DFS)?",
                "answer": "BFS visits all neighbor nodes at the current depth before moving deeper (using a Queue), while DFS explores as far as possible down each branch before backtracking (using a Stack or recursion)."
            },
            {
                "question": "Why does an Array provide O(1) access while a Linked List requires O(n) access?",
                "answer": "Array elements reside in contiguous memory enabling direct offset math (base + index * size); Linked Lists require pointer traversal node-by-node from the head."
            }
        ],
        "study_strategies": [
            "Draw memory diagrams of pointers and tree nodes before writing algorithmic code.",
            "Implement basic structures (Stack, Queue, LinkedList, BST) from scratch in Python.",
            "Analyze every function you write by stating its Big O time and space complexity."
        ],
        "suggested_next_topics": ["oop_principles", "python_basics", "sql_databases"]
    },

    # --------------------------------------------------------------------------
    # 9. OBJECT-ORIENTED PROGRAMMING
    # --------------------------------------------------------------------------
    "oop_principles": {
        "topic_name": "Object-Oriented Programming (OOP) & Design",
        "category": "Software Engineering",
        "keywords": [
            "oop", "object oriented programming", "classes", "objects", "encapsulation",
            "abstraction", "inheritance", "polymorphism", "solid principles",
            "design patterns", "singleton", "factory pattern", "interfaces"
        ],
        "explanation": (
            "Object-Oriented Programming is a software paradigm based on the concept of 'objects' containing data (attributes) and code (methods). "
            "It is anchored by the four pillars: Encapsulation (bundling data and restricting direct access via public methods), "
            "Abstraction (hiding complex internal implementation details and exposing clean interfaces), "
            "Inheritance (deriving new classes from existing classes to promote code reuse), and "
            "Polymorphism (allowing different objects to respond to the same method invocation in their own specific ways). "
            "The SOLID design principles guide developers in building scalable, maintainable, and decoupled object-oriented architectures."
        ),
        "key_points": [
            "Four Pillars: Encapsulation (data hiding), Abstraction (simplifying interface), Inheritance (code reuse / hierarchies), Polymorphism (multiple forms/method overriding).",
            "SOLID Principles: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion.",
            "Classes vs Objects: A class is the blueprint or prototype; an object is a concrete instance of that class allocated in memory.",
            "Composition over Inheritance: Favor composing objects with desired behaviors rather than creating deep, fragile inheritance hierarchies.",
            "Design Patterns: Reusable architectural templates categorized into Creational (Singleton, Factory), Structural (Adapter, Decorator), and Behavioral (Observer, Strategy)."
        ],
        "revision_questions": [
            {
                "question": "Explain Polymorphism with an intuitive software engineering example.",
                "answer": "Polymorphism allows different classes (e.g., Circle, Rectangle) to implement a common method (e.g., calculate_area()). A client can call shape.calculate_area() without needing to know the specific concrete class."
            },
            {
                "question": "What is the Single Responsibility Principle (SRP) in SOLID?",
                "answer": "A class should have one, and only one, reason to change — meaning it should encapsulate only a single focused functionality or domain responsibility."
            },
            {
                "question": "Why is 'Composition over Inheritance' often recommended?",
                "answer": "Inheritance tightly couples subclasses to parent implementations (the fragile base class problem); composition allows flexible behavior swapping at runtime without rigid class hierarchies."
            }
        ],
        "study_strategies": [
            "Refactor procedural code into classes with clear boundaries and well-named methods.",
            "Identify violations of SOLID in existing codebases and restructure them using interfaces.",
            "Study classic patterns like Factory, Observer, and Strategy by implementing concrete examples."
        ],
        "suggested_next_topics": ["python_basics", "django_fundamentals", "data_structures"]
    },

    # --------------------------------------------------------------------------
    # 10. DIGITAL LEARNING AND SMART EDUCATION
    # --------------------------------------------------------------------------
    "digital_learning": {
        "topic_name": "Digital Learning & SmartEdu Methodology",
        "category": "Educational Technology",
        "keywords": [
            "smartedu", "digital learning", "edtech", "active recall", "spaced repetition",
            "feynman technique", "formative assessment", "summative assessment", "lms",
            "learning analytics", "personalized learning", "study tips", "study strategies"
        ],
        "explanation": (
            "Modern digital learning harnesses cognitive science, deliberate practice, and technology to optimize student mastery. "
            "SmartEdu integrates structured curricula, self-paced modular lessons, multi-modal resources, and immediate quiz feedback. "
            "Proven cognitive techniques like Active Recall (actively stimulating memory recall rather than passive re-reading) and "
            "Spaced Repetition (revisiting concepts at increasing intervals) dramatically strengthen long-term retention. "
            "Formative assessments (quizzes during the learning process) guide study behavior, while Learning Analytics empower both students and instructors "
            "to identify knowledge gaps and personalize revision strategies."
        ),
        "key_points": [
            "Active Recall: Testing yourself on key questions forces the brain to retrieve information, creating stronger neural pathways than passive highlights.",
            "Spaced Repetition: Scheduling reviews over expanding intervals (1 day, 3 days, 1 week, 1 month) combats the Ebbinghaus forgetting curve.",
            "The Feynman Technique: Explain a complex topic in simple language as if teaching a beginner to uncover and repair personal conceptual gaps.",
            "Formative vs Summative: Formative assessments diagnose learning in progress; summative assessments evaluate overall final proficiency.",
            "Data-Driven Revision: Using analytics to target weak quiz topics rather than repeating already mastered material."
        ],
        "revision_questions": [
            {
                "question": "Why is Active Recall more effective than passive reading or highlighting?",
                "answer": "Passive reading creates an 'illusion of competence.' Active retrieval practice forces cognitive effort, which cements memory retention and highlights genuine gaps in comprehension."
            },
            {
                "question": "How does Spaced Repetition overcome the Ebbinghaus Forgetting Curve?",
                "answer": "By deliberately reviewing concepts just as they begin to fade from memory, the retention decay rate flattens, transferring knowledge from short-term to durable long-term memory."
            },
            {
                "question": "How do formative quizzes support self-regulated learning in an LMS?",
                "answer": "They provide immediate low-stakes feedback, enabling students to correct misconceptions before high-stakes evaluations and directing revision to specific weak areas."
            }
        ],
        "study_strategies": [
            "After every lesson, close your notes and write a 3-sentence summary completely from memory.",
            "Take the chapter quiz before reviewing the notes to leverage the pre-testing effect.",
            "Use the SmartEdu Demo AI Tutor to generate revision questions and test your active recall."
        ],
        "suggested_next_topics": ["python_basics", "django_fundamentals", "web_frontends"]
    }
}
