/**
 * Instant Demo Mode Fixtures
 * 
 * Provides complete, high-fidelity static data for 1-click interactive demo.
 * Zero backend latency, zero LLM calls, zero rate-limit or network dependencies.
 */

export const DEMO_PROFILE_ID = 'demo-profile-c56b7a2d-e490';
export const DEMO_USER_ID = 'demo-user-123e4567-e89b';
export const DEMO_VERSION_ID = 'demo-version-8910-abcd';

export const DEMO_USER = {
  id: DEMO_USER_ID,
  email: 'arjun.sharma@demo.hireme.ai',
  full_name: 'Arjun Sharma (Demo)',
  is_active: true,
  active_profile_id: DEMO_PROFILE_ID,
};

export const DEMO_CANDIDATE_PROFILE = {
  personal_info: {
    name: 'Arjun Sharma',
    email: 'arjun.sharma@demo.hireme.ai',
    phone: '+91 98765 43210',
    location: 'New Delhi, India (Open to Remote / Relocation)',
    linkedin: 'https://linkedin.com/in/arjun-sharma-cse',
    github: 'https://github.com/arjunsharma-dev',
    portfolio: 'https://arjunsharma.dev',
    summary: 'Aspiring Software & AI Engineer graduating from DTU (2025). Hands-on experience developing high-concurrency microservices, async FastAPI REST backends, and semantic search pipelines with vector embeddings. Passionate about production reliability, clean abstractions, and high-throughput systems.',
  },
  skills: [
    'Python',
    'FastAPI',
    'TypeScript',
    'React',
    'PostgreSQL',
    'Redis',
    'Docker',
    'Asyncio',
    'PyTorch',
    'Vector Embeddings',
    'LangChain',
    'Qdrant',
    'Celery',
    'REST APIs',
    'Git',
    'Linux',
    'SQL',
    'Tailwind CSS',
    'Node.js',
    'Microservices',
  ],
  education: [
    {
      institution: 'Delhi Technological University (DTU)',
      degree: 'B.Tech in Computer Science & Engineering',
      field_of_study: 'Computer Science',
      start_date: '2021',
      end_date: '2025',
      gpa: '8.8 / 10.0',
    },
  ],
  experience: [
    {
      company: 'TechFlow Solutions',
      title: 'Software Engineering Intern (Backend)',
      location: 'Bengaluru, India (Hybrid)',
      start_date: 'May 2024',
      end_date: 'Aug 2024',
      bullets: [
        'Built backend services using Python and connected databases to handle client search requests.',
        'Worked on caching system with Redis to make data retrieval faster for users.',
        'Containerized microservices with Docker and wrote unit test workflows for GitHub Actions CI/CD.',
      ],
    },
    {
      company: 'DataWave Labs',
      title: 'AI & Systems Intern',
      location: 'Remote',
      start_date: 'Jan 2024',
      end_date: 'Apr 2024',
      bullets: [
        'Built automated data ingestion pipelines in Python processing 2M+ daily events with Pandas and NumPy.',
        'Integrated OpenAI and open-source embedding tokenization pipelines to benchmark retrieval latency across text chunks.',
      ],
    },
  ],
  projects: [
    {
      name: 'NeuralSearch: Semantic Code & Doc Search Engine',
      description: 'End-to-end vector search engine for engineering codebases and documentation.',
      technologies: ['FastAPI', 'Qdrant', 'PyTorch', 'React', 'Docker'],
      bullets: [
        'Created a semantic search engine using FastAPI and vector database with a React UI.',
        'Indexed 500k+ technical documents with sub-80ms hybrid keyword and dense-vector recall.',
        'Implemented streaming LLM query reformulation to synthesize conversational answers from retrieved snippets.',
      ],
      url: 'https://github.com/arjunsharma-dev/neuralsearch',
    },
    {
      name: 'Distributed Task Queue & Rate Limiter',
      description: 'High-throughput async job processor with distributed rate limiting.',
      technologies: ['Python', 'Redis', 'Asyncio', 'Celery'],
      bullets: [
        'Developed a distributed task queue with token bucket rate limiting in Python.',
        'Sustained 2,500 req/sec peak throughput across asynchronous worker nodes without dropped messages.',
      ],
      url: 'https://github.com/arjunsharma-dev/async-task-engine',
    },
    {
      name: 'CloudSpend: Multi-Cloud FinOps Observability',
      description: 'Real-time cloud infrastructure cost attribution dashboard.',
      technologies: ['React', 'TypeScript', 'Tailwind CSS', 'PostgreSQL'],
      bullets: [
        'Designed interactive telemetry dashboard visualizing hourly compute spend across AWS and GCP instances.',
        'Built automated anomaly detection alerting users to unexpected cost spikes exceeding 15% delta.',
      ],
      url: 'https://github.com/arjunsharma-dev/cloudspend',
    },
  ],
  certifications: [
    {
      name: 'DeepLearning.AI: Deep Learning Specialization',
      issuer: 'Coursera',
      date: '2023',
    },
    {
      name: 'AWS Certified Cloud Practitioner (CLF-C02)',
      issuer: 'Amazon Web Services',
      date: '2024',
    },
  ],
  achievements: [
    'Smart India Hackathon (SIH) 2023 Winner: 1st place in AI Track out of 1,200+ competing university teams.',
    'Competitive Programming: Peak Rating 2048 (Top 2%) on LeetCode; 750+ algorithmic problems solved.',
    'Academic Excellence Scholarship recipient for top 5% semester GPA at DTU.',
  ],
};

export const DEMO_JOBS_LIST = [
  {
    id: 'demo-job-1-anthropic',
    title: 'Associate AI Software Engineer (Early Career)',
    company: 'Anthropic',
    location: 'San Francisco, CA / Remote',
    source: 'ashby',
    apply_url: 'https://jobs.ashbyhq.com/anthropic',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(), // 6 hours ago
    fresher_score: 95,
    match_percent: 94,
    matched_skills: ['Python', 'FastAPI', 'PyTorch', 'Vector Embeddings', 'Redis', 'Docker'],
    missing_skills: ['Kubernetes', 'Ray', 'Triton'],
    remote: true,
    reason: 'Exceptional fit for early-career AI SWE: values Python async services, vector retrieval, and hands-on ML systems.',
    description: `About the Role:
Anthropic is seeking an Associate AI Software Engineer to join our Core Systems & Inference tooling team. You will collaborate directly with research and product engineers to build, scale, and optimize the data and serving pipelines that power Claude.

What You Will Do:
- Design and maintain high-throughput backend APIs and internal developer tools using Python, FastAPI, and asynchronous workflows.
- Build vector indexing pipelines, evaluation harnesses, and dataset preparation workers for next-generation foundation models.
- Implement telemetry, rate-limiting, and caching layers using Redis and PostgreSQL to optimize inference roundtrip latency.
- Write robust, well-tested code with rigorous CI/CD automation.

Requirements:
- Bachelor's degree in Computer Science, Software Engineering, or related technical field (graduating 2024–2025).
- Strong proficiency in modern Python (asyncio, type hints, pydantic, FastAPI).
- Solid foundation in data structures, algorithms, and distributed systems fundamentals.
- Hands-on experience with vector embeddings, PyTorch, or LLM application pipelines is a strong plus.`,
  },
  {
    id: 'demo-job-2-scaleai',
    title: 'Junior Machine Learning Engineer - Data Engine',
    company: 'Scale AI',
    location: 'San Francisco, CA / Remote',
    source: 'greenhouse',
    apply_url: 'https://boards.greenhouse.io/scaleai',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 18).toISOString(),
    fresher_score: 92,
    match_percent: 91,
    matched_skills: ['Python', 'Docker', 'PostgreSQL', 'PyTorch', 'REST APIs', 'Git'],
    missing_skills: ['Kafka', 'Spark', 'Airflow'],
    remote: true,
    reason: 'Zero-to-two years role matching candidate data pipeline and Python backend strength.',
    description: `Scale AI is looking for a Junior Machine Learning Engineer to help scale our Data Engine. You will build automated data validation, ingestion pipelines, and ML feedback loops that train world-class AI models.

Requirements:
- B.S. in Computer Science or quantitative discipline.
- Proven fluency in Python, SQL, and containerized deployments with Docker.
- Experience with dataset processing and microservices architecture.`,
  },
  {
    id: 'demo-job-3-stripe',
    title: 'Software Engineer - Early Career (University Graduate)',
    company: 'Stripe',
    location: 'Seattle, WA / Remote',
    source: 'greenhouse',
    apply_url: 'https://stripe.com/jobs',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    fresher_score: 90,
    match_percent: 89,
    matched_skills: ['Python', 'REST APIs', 'PostgreSQL', 'Redis', 'Git', 'Linux'],
    missing_skills: ['Ruby', 'Java', 'Distributed Transactions'],
    remote: true,
    reason: 'Stripe university grad pipeline focusing on CS core fundamentals, APIs, and systems thinking.',
    description: `Stripe's Early Career engineering program provides mentorship, accelerated onboarding, and ownership over critical global financial infrastructure.

What you will do:
- Develop reliable backend APIs processing hundreds of billions in global commerce.
- Build fault-tolerant distributed services with high availability and automated testing.`,
  },
  {
    id: 'demo-job-4-datadog',
    title: 'Software Engineer I - Core Backend Systems',
    company: 'Datadog',
    location: 'New York, NY / Remote',
    source: 'greenhouse',
    apply_url: 'https://careers.datadoghq.com',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 30).toISOString(),
    fresher_score: 88,
    match_percent: 88,
    matched_skills: ['Python', 'Docker', 'Redis', 'Linux', 'Microservices'],
    missing_skills: ['Go', 'Kafka', 'eBPF'],
    remote: true,
    reason: 'Early career position ideal for candidates with asynchronous backend and caching exposure.',
    description: `Join Datadog's Core Backend team to build scalable real-time observability telemetry pipelines.`,
  },
  {
    id: 'demo-job-5-vercel',
    title: 'Junior Full-Stack Engineer (DX & Frameworks)',
    company: 'Vercel',
    location: 'Remote (Worldwide)',
    source: 'ashby',
    apply_url: 'https://vercel.com/careers',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 38).toISOString(),
    fresher_score: 91,
    match_percent: 86,
    matched_skills: ['TypeScript', 'React', 'Node.js', 'Tailwind CSS', 'Git'],
    missing_skills: ['Next.js App Router Internals', 'Rust'],
    remote: true,
    reason: 'Remote-first culture looking for passionate young builders with clean TypeScript and React fundamentals.',
    description: `Vercel is seeking a Junior Full-Stack Engineer to improve the developer experience of web creators worldwide.`,
  },
  {
    id: 'demo-job-6-figma',
    title: 'Associate Software Engineer - Web Platform',
    company: 'Figma',
    location: 'San Francisco, CA / Hybrid',
    source: 'greenhouse',
    apply_url: 'https://www.figma.com/careers',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
    fresher_score: 87,
    match_percent: 85,
    matched_skills: ['TypeScript', 'React', 'REST APIs', 'Git', 'Linux'],
    missing_skills: ['WebAssembly', 'C++ Graphics'],
    remote: false,
    reason: 'Structured early career mentorship program focusing on browser systems and frontend architecture.',
    description: `Figma's early career cohort builds the multiplayer design platform used by millions of product teams.`,
  },
  {
    id: 'demo-job-7-supabase',
    title: 'Junior Backend & Developer Advocate Engineer',
    company: 'Supabase',
    location: 'Remote',
    source: 'ashby',
    apply_url: 'https://supabase.com/careers',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 52).toISOString(),
    fresher_score: 89,
    match_percent: 84,
    matched_skills: ['PostgreSQL', 'TypeScript', 'Docker', 'Python', 'REST APIs'],
    missing_skills: ['Elixir', 'pgvector internals'],
    remote: true,
    reason: 'Open source first team; candidate project portfolio and PostgreSQL/Docker profile match closely.',
    description: `Build open source developer tools, sample applications, and database extensions for PostgreSQL enthusiasts.`,
  },
  {
    id: 'demo-job-8-retool',
    title: 'Full-Stack Software Engineer (New Grad 2025)',
    company: 'Retool',
    location: 'San Francisco, CA',
    source: 'lever',
    apply_url: 'https://jobs.lever.co/retool',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 60).toISOString(),
    fresher_score: 85,
    match_percent: 82,
    matched_skills: ['React', 'TypeScript', 'Node.js', 'PostgreSQL'],
    missing_skills: ['GraphQL', 'Kubernetes'],
    remote: false,
    reason: 'Explicit new grad cohort role emphasizing high-velocity shipping and software craftsmanship.',
    description: `Retool empowers companies to build mission-critical internal software 10x faster.`,
  },
  {
    id: 'demo-job-9-notion',
    title: 'Software Engineer - University Graduate 2025',
    company: 'Notion',
    location: 'San Francisco, CA / Remote',
    source: 'greenhouse',
    apply_url: 'https://www.notion.so/careers',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 70).toISOString(),
    fresher_score: 86,
    match_percent: 81,
    matched_skills: ['TypeScript', 'React', 'PostgreSQL', 'Redis'],
    missing_skills: ['Kotlin', 'Android Native'],
    remote: true,
    reason: 'Early career opening for engineers enthusiastic about connected workspace collaboration.',
    description: `Notion is looking for graduating university seniors to join our product and infrastructure pods.`,
  },
  {
    id: 'demo-job-10-pinecone',
    title: 'Associate Systems Engineer - Vector Database Infrastructure',
    company: 'Pinecone',
    location: 'San Francisco, CA / Remote',
    source: 'ashby',
    apply_url: 'https://www.pinecone.io/careers',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 76).toISOString(),
    fresher_score: 83,
    match_percent: 80,
    matched_skills: ['Python', 'Docker', 'Linux', 'Vector Embeddings'],
    missing_skills: ['C++', 'Rust', 'Raft Consensus'],
    remote: true,
    reason: 'Candidate has built an actual vector search engine with Qdrant and understands embedding spaces.',
    description: `Help build the vector search infrastructure underpinning the generative AI transformation.`,
  },
  {
    id: 'demo-job-11-ramp',
    title: 'Software Engineer I - Financial Infrastructure',
    company: 'Ramp',
    location: 'New York, NY / Remote',
    source: 'ashby',
    apply_url: 'https://ramp.com/careers',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 85).toISOString(),
    fresher_score: 84,
    match_percent: 79,
    matched_skills: ['Python', 'PostgreSQL', 'FastAPI', 'Git'],
    missing_skills: ['Accounting Engines', 'Ledger Architecture'],
    remote: true,
    reason: 'Ramp values Python and async backend engineering for modern corporate spend automation.',
    description: `Build high-reliability financial products that automate enterprise card operations and savings.`,
  },
  {
    id: 'demo-job-12-postman',
    title: 'Associate Software Engineer - API Platform',
    company: 'Postman',
    location: 'Bangalore, India / Remote',
    source: 'lever',
    apply_url: 'https://www.postman.com/company/careers',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 92).toISOString(),
    fresher_score: 88,
    match_percent: 78,
    matched_skills: ['REST APIs', 'Node.js', 'TypeScript', 'Git'],
    missing_skills: ['OpenAPI 3.1 tooling', 'Electron'],
    remote: true,
    reason: 'Bangalore-based early career opportunity focused on developer tooling and REST API workflows.',
    description: `Postman is looking for early-career software engineers to empower 30 million API developers.`,
  },
  {
    id: 'demo-job-13-perplexity',
    title: 'Early Career AI Engineer - Retrieval & Indexing',
    company: 'Perplexity AI',
    location: 'San Francisco, CA',
    source: 'ashby',
    apply_url: 'https://jobs.ashbyhq.com/perplexity',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 98).toISOString(),
    fresher_score: 82,
    match_percent: 77,
    matched_skills: ['Python', 'FastAPI', 'PyTorch', 'Vector Embeddings'],
    missing_skills: ['Web Crawling at Scale', 'ElasticSearch'],
    remote: false,
    reason: 'Search and retrieval focus aligns cleanly with candidate semantic search project experience.',
    description: `Build the conversational answer engine answering millions of questions in real-time.`,
  },
  {
    id: 'demo-job-14-cloudflare',
    title: 'Systems Engineer - Emerging Tech (Early Career)',
    company: 'Cloudflare',
    location: 'Austin, TX / Remote',
    source: 'greenhouse',
    apply_url: 'https://www.cloudflare.com/careers',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 110).toISOString(),
    fresher_score: 85,
    match_percent: 75,
    matched_skills: ['Linux', 'Docker', 'Python', 'Git'],
    missing_skills: ['Rust', 'eBPF', 'BGP'],
    remote: true,
    reason: 'Hands-on Linux, Docker, and networking foundations match Cloudflare early career criteria.',
    description: `Help build a faster, more secure internet on Cloudflare's global edge network.`,
  },
  {
    id: 'demo-job-15-glean',
    title: 'Junior Backend Engineer - Enterprise Search',
    company: 'Glean',
    location: 'Palo Alto, CA / Remote',
    source: 'greenhouse',
    apply_url: 'https://www.glean.com/careers',
    posted_at: new Date(Date.now() - 1000 * 60 * 60 * 125).toISOString(),
    fresher_score: 81,
    match_percent: 74,
    matched_skills: ['Python', 'PostgreSQL', 'Docker', 'REST APIs'],
    missing_skills: ['Enterprise Connectors', 'SAML SSO'],
    remote: true,
    reason: 'Glean builds AI enterprise search; strong overlap with candidate background in search indexing.',
    description: `Connect and index enterprise workplace data across Slack, Google Drive, Jira, and GitHub.`,
  },
];

export const DEMO_TAILORED_RESULT = {
  version_id: DEMO_VERSION_ID,
  tailored_json: DEMO_CANDIDATE_PROFILE,
  pdf_path: '/demo_tailored_resume.pdf',
  ats_score: 91,
  fidelity_score: 100,
  coverage_percent: 91,
  matched_keywords: [
    'Python',
    'FastAPI',
    'Vector Embeddings',
    'PyTorch',
    'Redis',
    'Docker',
    'PostgreSQL',
    'Asyncio',
    'REST APIs',
    'LangChain',
  ],
  gaps: ['Kubernetes', 'Ray', 'Triton'],
  ats_report: {
    initial_score: 68,
    tailored_score: 91,
    score_delta: '+23 pts',
    ats_checks: {
      contact_info: true,
      quantified_metrics: true,
      action_verbs: true,
      keyword_match: true,
      format_clean: true,
      no_tables_or_columns: true,
    },
    recommendations: [
      'Successfully aligned bullet action verbs with Anthropic JD keywords (FastAPI, Redis, vector indexing).',
      'Preserved 100% of candidate verifiable dates, DTU education, and internship companies.',
      'Quantified p99 search latency reduction (-42%) and cache hit ratio (94.6%).',
    ],
  },
  change_log: [
    {
      bullet_id: 'exp_0_b0',
      entity: 'TechFlow Solutions (Work Experience)',
      original: 'Built backend services using Python and connected databases to handle client search requests.',
      edited: 'Architected high-throughput async REST endpoints in FastAPI & Python, optimizing database queries to reduce p99 search latency by 42%.',
      operations: ['ACTION_VERB_ENHANCEMENT', 'METRIC_QUANTIFICATION', 'JD_KEYWORD_ALIGNMENT'],
      keywords_added: ['FastAPI', 'async REST endpoints', 'p99 latency'],
      retention_ratio: 0.82,
      status: 'accepted',
    },
    {
      bullet_id: 'exp_0_b1',
      entity: 'TechFlow Solutions (Work Experience)',
      original: 'Worked on caching system with Redis to make data retrieval faster for users.',
      edited: 'Implemented a multi-tier Redis caching layer for vector embeddings and search metadata, elevating cache hit ratio to 94.6%.',
      operations: ['TECHNICAL_SPECIFICATION', 'QUANTIFICATION'],
      keywords_added: ['Redis caching layer', 'vector embeddings', 'cache hit ratio'],
      retention_ratio: 0.79,
      status: 'accepted',
    },
    {
      bullet_id: 'proj_0_b0',
      entity: 'NeuralSearch (Key Project)',
      original: 'Created a semantic search engine using FastAPI and vector database with a React UI.',
      edited: 'Engineered an end-to-end semantic search engine integrating Qdrant vector database and PyTorch embeddings, indexing 500k+ technical documents with sub-80ms recall.',
      operations: ['SPECIFICITY_BOOST', 'SCALE_QUANTIFICATION'],
      keywords_added: ['Qdrant', 'PyTorch embeddings', 'sub-80ms recall'],
      retention_ratio: 0.85,
      status: 'accepted',
    },
    {
      bullet_id: 'proj_1_b0',
      entity: 'Distributed Task Queue (Key Project)',
      original: 'Developed a distributed task queue with token bucket rate limiting in Python.',
      edited: 'Developed distributed task worker engine using Celery and Redis with sliding-window rate limiting, sustaining 2,500 req/sec without queue overflow.',
      operations: ['PRECISION_MAPPING', 'THROUGHPUT_METRIC'],
      keywords_added: ['sliding-window rate limiting', 'sustaining 2,500 req/sec'],
      retention_ratio: 0.88,
      status: 'accepted',
    },
  ],
};

export const DEMO_LATEX_SOURCE = `%-------------------------
% Tailored Resume - Arjun Sharma
% Optimized for Anthropic: Associate AI Software Engineer
% Generated via HireMe AI Minimal-Edit Engine
%-------------------------

\\documentclass[letterpaper,11pt]{article}
\\usepackage{latexsym}
\\usepackage[empty]{fullpage}
\\usepackage{titlesec}
\\usepackage{marvosym}
\\usepackage[usenames,dvipsnames]{color}
\\usepackage{verbatim}
\\usepackage{enumitem}
\\usepackage[hidelinks]{hyperref}
\\usepackage{fancyhdr}
\\usepackage[english]{babel}
\\usepackage{tabularx}

\\pagestyle{fancy}
\\fancyhf{}
\\renewcommand{\\headrulewidth}{0pt}
\\renewcommand{\\footrulewidth}{0pt}

\\addtolength{\\oddsidemargin}{-0.5in}
\\addtolength{\\evensidemargin}{-0.5in}
\\addtolength{\\textwidth}{1in}
\\addtolength{\\topmargin}{-.5in}
\\addtolength{\\textheight}{1.0in}

\\urlstyle{same}
\\raggedbottom
\\raggedright
\\setlength{\\tabcolsep}{0in}

\\titleformat{\\section}{
  \\vspace{-4pt}\\scshape\\raggedright\\large
}{}{0em}{}[\\color{black}\\titlerule \\vspace{-5pt}]

\\begin{document}

\\begin{center}
    \\textbf{\\Huge \\scshape Arjun Sharma} \\\\ \\vspace{1pt}
    \\small New Delhi, India $|$ +91 98765 43210 $|$ \\href{mailto:arjun.sharma@demo.hireme.ai}{\\underline{arjun.sharma@demo.hireme.ai}} $|$ 
    \\href{https://linkedin.com/in/arjun-sharma-cse}{\\underline{linkedin.com/in/arjun-sharma-cse}} $|$
    \\href{https://github.com/arjunsharma-dev}{\\underline{github.com/arjunsharma-dev}}
\\end{center}

\\section{Education}
  \\resumeSubHeadingListStart
    \\resumeSubheading
      {Delhi Technological University (DTU)}{New Delhi, India}
      {Bachelor of Technology in Computer Science \\& Engineering; GPA: 8.8/10.0}{2021 -- 2025}
  \\resumeSubHeadingListEnd

\\section{Technical Skills}
 \\begin{itemize}[leftmargin=0.15in, label={}]
    \\small{\\item{
     \\textbf{Languages}{: Python, TypeScript, JavaScript, SQL, C++, Go (Basic)} \\\\
     \\textbf{Frameworks \\& Tools}{: FastAPI, React, Docker, Redis, PostgreSQL, Celery, Linux, Git, REST APIs} \\\\
     \\textbf{AI \\& Retrieval}{: PyTorch, LangChain, Vector Embeddings, Qdrant, NumPy, Pandas}
    }}
 \\end{itemize}

\\section{Experience}
  \\resumeSubHeadingListStart
    \\resumeSubheading
      {Software Engineering Intern (Backend)}{May 2024 -- Aug 2024}
      {TechFlow Solutions}{Bengaluru, India (Hybrid)}
      \\resumeItemListStart
        \\resumeItem{Architected high-throughput async REST endpoints in FastAPI \\& Python, optimizing database queries to reduce p99 search latency by 42\\%.}
        \\resumeItem{Implemented a multi-tier Redis caching layer for vector embeddings and search metadata, elevating cache hit ratio to 94.6\\%.}
        \\resumeItem{Containerized 4 microservices with multi-stage Dockerfiles and automated integration testing pipelines in GitHub Actions.}
      \\resumeItemListEnd

    \\resumeSubheading
      {AI \\& Systems Intern}{Jan 2024 -- Apr 2024}
      {DataWave Labs}{Remote}
      \\resumeItemListStart
        \\resumeItem{Engineered automated data preprocessing pipeline handling 2M+ records daily using Pandas and NumPy with zero data drops.}
        \\resumeItem{Integrated OpenAI \\& HuggingFace tokenization pipelines for document chunking, benchmarking embedding retrieval speeds across models.}
      \\resumeItemListEnd
  \\resumeSubHeadingListEnd

\\section{Key Projects}
  \\resumeSubHeadingListStart
    \\resumeProjectHeading
      {\\textbf{NeuralSearch: Semantic Code \\& Doc Search Engine} $|$ \\emph{FastAPI, Qdrant, PyTorch, React, Docker}}{2024}
      \\resumeItemListStart
        \\resumeItem{Engineered an end-to-end semantic search engine integrating Qdrant vector database and PyTorch embeddings, indexing 500k+ technical documents with sub-80ms recall.}
        \\resumeItem{Designed responsive React frontend with query highlighting and latency telemetry dashboards.}
      \\resumeItemListEnd

    \\resumeProjectHeading
      {\\textbf{Distributed Task Queue \\& Rate Limiter} $|$ \\emph{Python, Redis, Asyncio, Celery}}{2024}
      \\resumeItemListStart
        \\resumeItem{Developed distributed task worker engine using Celery and Redis with sliding-window rate limiting, sustaining 2,500 req/sec without queue overflow.}
        \\resumeItem{Implemented dead-letter exchange and retry backoff mechanics ensuring 99.99\\% message delivery reliability.}
      \\resumeItemListEnd
  \\resumeSubHeadingListEnd

\\section{Achievements \\& Honors}
 \\begin{itemize}[leftmargin=0.15in, label={}]
    \\small{\\item{
     \\textbf{Smart India Hackathon (SIH) 2023 Winner}{: 1st place in AI track out of 1,200+ competing engineering teams.} \\\\
     \\textbf{Competitive Programming}{: Peak rating 2048 (Top 2\\%) on LeetCode; solved 750+ data structure \\& algorithm problems.}
    }}
 \\end{itemize}

\\end{document}
`;

export const DEMO_APPLICATIONS_LIST = [
  {
    id: 'demo-app-1',
    profile_id: DEMO_PROFILE_ID,
    job_id: 'demo-job-1-anthropic',
    job_title: 'Associate AI Software Engineer (Early Career)',
    company: 'Anthropic',
    status: 'saved',
    applied_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    match_score: 94,
    notes: 'Tailored resume generated with 91 ATS score. Ready to apply on Ashby board.',
  },
  {
    id: 'demo-app-2',
    profile_id: DEMO_PROFILE_ID,
    job_id: 'demo-job-2-scaleai',
    job_title: 'Junior Machine Learning Engineer - Data Engine',
    company: 'Scale AI',
    status: 'applied',
    applied_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    match_score: 91,
    notes: 'Application submitted via Greenhouse job portal.',
  },
  {
    id: 'demo-app-3',
    profile_id: DEMO_PROFILE_ID,
    job_id: 'demo-job-3-stripe',
    job_title: 'Software Engineer - Early Career',
    company: 'Stripe',
    status: 'interviewing',
    applied_at: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(),
    match_score: 89,
    notes: 'Technical recruiter screen scheduled for Friday.',
  },
];
