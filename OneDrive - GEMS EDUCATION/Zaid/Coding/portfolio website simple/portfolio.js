// Simple portfolio functionality with complete card data

// Complete card data from original Django site
const cardData = {
    'AWS Virtual Internship': {
        rating: 'July 2025',
        title: 'AWS Virtual Internship',
        description: 'Completed cloud-focused challenges, strengthening understanding of scalable solutions and modern infrastructure through real-world simulations.',
        sections: {
            'Key Learning Outcomes': [
                'Mastered the role of Solutions Architecture at AWS',
                'Implemented scalable cloud architectures',
                'Learned infrastructure as code with CloudFormation',
                'Gained experience with AWS Lambda serverless computing',
                'Understood cloud security best practices'
            ],
            'Projects Completed': [
                'Built a scalable web application on AWS',
                'Implemented CI/CD pipeline using AWS CodePipeline',
                'Created monitoring dashboards with CloudWatch',
                'Designed cost-optimized cloud solutions'
            ],
            'Skills Developed': [
                'Cloud Architecture Diagram',
                'AWS Pricing',
                'Technical Communication',
                'Cost Optimization',
                'Security Implementation'
            ]
        },
        links: [
            { text: 'View Certificate', url: '#' }
        ]
    },

    'Accenture Job Simulation': {
        rating: 'June 2024',
        title: 'Accenture Job Simulation',
        description: 'Engaged in consulting-style problem solving, honing skills in client analysis, digital transformation, and strategic planning.',
        sections: {
            'Consulting Skills Developed': [
                'Client requirement analysis and documentation',
                'Business process optimization strategies',
                'Digital transformation roadmap creation',
                'Data-driven decision making frameworks',
                'Stakeholder communication and presentation'
            ],
            'Technical Applications': [
                'Process automation solution design',
                'Data analytics dashboard creation',
                'Technology implementation planning',
                'ROI analysis and financial modeling'
            ],
            'Key Achievements': [
                'Successfully completed 5 client simulation cases',
                'Achieved top 10% ranking in problem-solving assessments',
                'Delivered compelling business transformation proposals'
            ]
        },
        links: [
            { text: 'View Certificate', url: '#' }
        ]
    },

    'JP Morgan & Chase Program': {
        rating: 'July 2024',
        title: 'JP Morgan & Chase Program',
        description: 'Explored financial technology simulations with data-driven insights and solutions relevant to global banking systems.',
        sections: {
            'Finance & Analysis Skills Developed': [
                'Equity and debt market research',
                'Financial modeling and valuation techniques',
                'Risk identification and mitigation strategies',
                'Client portfolio analysis and advisory',
                'Presentation of investment recommendations'
            ],
            'Technical Applications': [
                'Excel-based financial modeling',
                'Data visualization for market insights',
                'Scenario and sensitivity analysis',
                'Application of corporate finance principles'
            ],
            'Key Achievements': [
                'Completed multiple investment banking case studies',
                'Ranked in top 15% for financial problem-solving accuracy',
                'Delivered actionable recommendations on client investment strategies'
            ]
        },
        links: [
            { text: 'View Certificate', url: '#' }
        ]
    },

    'The Forage Programs': {
        rating: '2024 - 2025',
        title: 'The Forage Programs',
        description: 'Completed multiple virtual internships gaining practical exposure to real-world industry tasks across various sectors.',
        sections: {
            'Skills Developed': [
                'Problem-solving and critical thinking in business contexts',
                'Client communication and requirement analysis',
                'Digital transformation and process optimization',
                'Financial modeling, valuation, and risk analysis',
                'Professional presentation and structured reporting'
            ],
            'Technical Applications': [
                'Data analytics and visualization',
                'Excel-based financial modeling',
                'Process automation strategies',
                'Scenario-based consulting frameworks'
            ],
            'Key Achievements': [
                'Successfully completed job simulations with top global firms',
                'Ranked among top-performing candidates in assessments',
                'Delivered actionable business and financial solutions'
            ]
        },
        links: [
            { text: 'View Certificates', url: '#' }
        ]
    },

    'Python Ecosystem': {
        rating: 'Intermediate',
        title: 'Python Ecosystem',
        description: 'Django, Flask & SQLAlchemy for async tasks, database integration, featuring user authentication, data management and API handling, pytest for testing, and extensive experience with Python standard library.',
        sections: {
            'Skills Developed': [
                'Object-oriented Python programming',
                'Django MVC framework and templating',
                'REST API development with Django REST Framework',
                'Database integration with ORM',
                'Error handling, testing, and debugging'
            ],
            'Technical Applications': [
                'Full-stack web development',
                'Data modeling and SQL queries via ORM',
                'Integration with front-end templates',
                'Authentication and user management'
            ],
            'Key Achievements': [
                'Built a personal finance tracker web app with Django',
                'Applied clean architecture and modular design',
                'Built a Voice Virtual Assistant with a python backend'
            ]
        },
        links: [
            { text: 'GitHub Projects', url: 'https://github.com/zaid3004' },
            { text: 'Live Demo Of VVA', url: 'https://orion-vva.vercel.app' }
        ]
    },

    'JavaScript, HTML and CSS': {
        rating: 'Advanced',
        title: 'JavaScript, HTML And CSS',
        description: 'Strong skills in modern HTML & CSS. Created dynamic user interfaces and single-page applications with responsive design.',
        sections: {
            'Skills Developed': [
                'Responsive web design with Flexbox and Grid',
                'Cross-browser compatibility and accessibility',
                'Custom animations and transitions',
                'Semantic HTML for structured content',
                'Reusable and modular CSS design patterns'
            ],
            'Technical Applications': [
                'Media queries for multi-device support',
                'CSS variables and custom properties',
                'Form styling and UI components',
                'Optimized layouts for performance',
                'Integration with modern frontend frameworks'
            ],
            'Key Achievements': [
                'Developed fully responsive portfolio and project websites',
                'Created consistent design systems with reusable components',
                'Implemented clean, scalable CSS architecture'
            ]
        },
        links: []
    },

    'Database Management': {
        rating: 'Beginner',
        title: 'Database Management',
        description: 'Newbie with PostgreSQL, MySQL, and MongoDB. Learning to design complex database schemas and optimized SQL queries.',
        sections: {
            'SQL & Relational Databases': [
                'Schema design and normalization',
                'CRUD operations and joins',
                'Constraints, keys, and relationships',
                'Optimized queries for performance'
            ],
            'NoSQL & Alternatives': [
                'Document-based storage systems',
                'Handling unstructured data',
                'Indexing for faster queries',
                'Deciding between relational and non-relational models'
            ],
            'Projects': [
                'Integrated PostgreSQL and SQLite in full-stack apps',
                'Database-backed finance tracker application',
                'Implemented data persistence and backup strategies'
            ]
        },
        links: []
    },

    'Version Control': {
        rating: 'Advanced',
        title: 'Version Control',
        description: 'Proficient with Git and GitHub workflows. Managed repositories and collaborated using branching strategies and code reviews.',
        sections: {
            'Skills Developed': [
                'Git commit, push, pull, branch, and merge',
                'Collaborative workflows with GitHub',
                'Code review practices',
                'Versioning and release management'
            ],
            'Technical Applications': [
                'Team-based project development',
                'Managing multiple branches and resolving conflicts',
                'Integrating CI/CD pipelines'
            ],
            'Key Achievements': [
                'Successfully managed multiple project repositories',
                'Implemented efficient branching and merging strategies',
                'Maintained clean project history for collaborative work'
            ]
        },
        links: [
            { text: 'View GitHub', url: 'https://github.com/zaid3004' }
        ]
    },

    'Portfolio Website': {
        rating: "Featured - You're Here!",
        title: 'Portfolio Website',
        description: 'Modern portfolio site with responsive design, Netflix-style layout, and dynamic content sections.',
        sections: {
            'Skills Applied': [
                'Full-stack web development',
                'Responsive front-end design',
                'Template-driven dynamic content',
                'UI/UX optimization and layout design'
            ],
            'Technical Applications': [
                'Django templating engine',
                'CSS Flexbox and Grid for layouts',
                'Interactive elements and animations'
            ],
            'Key Achievements': [
                'Showcased multiple projects in a professional layout',
                'Implemented a scalable template-based design'
            ]
        },
        links: [
            { text: 'View Repository', url: 'https://github.com/zaid3004/portfolio-website' }
        ]
    },

    'Voice Virtual Assistant': {
        rating: 'Orion VVA - Public',
        title: 'Voice Virtual Assistant',
        description: 'A web-based assistant that processes spoken commands for tasks like time, date, and information retrieval, presented through a modern UI.',
        sections: {
            'Skills Applied': [
                'Speech recognition and processing',
                'Python-based command execution',
                'Dynamic web interface integration',
                'Real-time response handling'
            ],
            'Technical Applications': [
                'SpeechRecognition and pyttsx3 in Python',
                'JSON for conversation logging',
                'Integration with Flask/Django front-end'
            ],
            'Key Achievements': [
                'Built a functional personal assistant prototype',
                'Handled multiple commands and edge cases successfully'
            ]
        },
        links: [
            { text: 'View Live Demo', url: 'https://orion-vva.vercel.app' },
            { text: 'View Repository', url: 'https://github.com/zaid3004/orion-vva' }
        ]
    },

    'Finance Tracker': {
        rating: 'Web Application - Not Public',
        title: 'Finance Tracker',
        description: 'A robust app that manages income and expenses, supports multiple accounts, filtering, chart visualizations, Excel import/export, and currency conversion.',
        sections: {
            'Skills Applied': [
                'Python and Tkinter GUI development',
                'Data management with CSV/Excel',
                'Filtering, sorting, and visualization of financial data'
            ],
            'Technical Applications': [
                'Matplotlib for charts',
                'Pandas for data manipulation',
                'Multi-account and currency support'
            ],
            'Key Achievements': [
                'Built a complete finance management solution',
                'Implemented Excel import/export with auto-formatting',
                'Created dynamic graphs for user-friendly analytics'
            ]
        },
        links: [
            { text: 'View Code', url: 'https://github.com/zaid3004/finance-tracker' }
        ]
    },

    'QR Code Generator': {
        rating: 'Image Generator - Not Public',
        title: 'QR Code Generator',
        description: 'Python-based app that creates QR codes from text, displays them, and allows saving in PNG or PDF formats.',
        sections: {
            'Skills Applied': [
                'Python GUI development with Tkinter',
                'QR code generation and display',
                'File handling and export options'
            ],
            'Technical Applications': [
                'qrcode and PIL libraries',
                'PDF and PNG export functionality',
                'Dynamic user input processing'
            ],
            'Key Achievements': [
                'Developed an interactive QR code generator',
                'Enabled multi-format saving and user-friendly interface'
            ]
        },
        links: [
            { text: 'View Code', url: 'https://github.com/zaid3004/qr-generator' }
        ]
    },

    'Password Strength Checker': {
        rating: 'Utility',
        title: 'Password Strength Checker',
        description: 'A Python CLI tool that evaluates password security by detecting weak patterns, measuring complexity, and guiding users toward creating stronger choices.',
        sections: {
            'Functionality': [
                'Checks against common password lists',
                'Analyzes character variety and length',
                'Detects weak sequential patterns',
                'Generates strength feedback'
            ],
            'Technical Implementation': [
                'Developed with Python standard libraries',
                'Regex for pattern recognition',
                'CLI-based secure input handling',
                'Extensible design for new rules'
            ],
            'Applications': [
                'Improves user awareness of security',
                'Can be integrated into login systems',
                'Provides educational feedback on security'
            ]
        },
        links: [
            { text: 'View Code', url: '#' }
        ]
    },

    'Computer Science Fundamentals': {
        rating: 'Core',
        title: 'Computer Science Fundamentals',
        description: 'Coursework covering OOP, data structures, algorithms, and computational theory with practical coding assignments.',
        sections: {
            'Core Topics': [
                'Object-Oriented Programming (OOP)',
                'Data Structures and Algorithms',
                'Computational theory and complexity',
                'Problem-solving with pseudocode'
            ],
            'Technical Skills': [
                'Algorithm design and analysis',
                'Debugging and testing techniques',
                'Memory and runtime optimization',
                'Abstract data type implementation'
            ],
            'Coursework Projects': [
                'Implemented sorting and search algorithms',
                'Built OOP-based mini applications',
                'Applied computational theory concepts',
                'Developed structured programming assignments'
            ]
        },
        links: [
            { text: 'View Coursework', url: '#' }
        ]
    },

    'Harvard CS50W': {
        rating: '2025',
        title: 'Harvard CS50W: Web Development With Python & JavaScript',
        description: 'Completed Harvard\'s CS50W course, building expertise in modern web development including backend, frontend, and database integration.',
        sections: {
            'Core Skills Gained': [
                'Flask-based backend development',
                'Advanced SQL and database design',
                'REST API creation and integration',
                'JavaScript for dynamic web functionality',
                'Scalable and secure application design'
            ],
            'Key Projects': [
                'HTML and CSS Google Search Platform',
                'Full-stack wiki application with editing features with Django'
            ]
        },
        links: [
            { text: 'Github Projects', url: '#' },
            { text: 'View Course', url: '#' },
            { text: 'View Certificate', url: '#' }
        ]
    },

    'VVA Research Paper': {
        rating: 'Research',
        title: 'Aurora VVA Research Paper',
        description: 'Team-authored research paper on building an AI-powered virtual assistant using speech recognition, NLP, and Python-based automation.',
        sections: {
            'Research Focus': [
                'Speech recognition techniques',
                'Natural Language Processing (NLP)',
                'Task automation in Python',
                'AI-driven conversational design'
            ],
            'Methodology': [
                'Agile project workflow',
                'Collaborative research writing',
                'Experimentation and prototyping',
                'Performance evaluation and testing'
            ],
            'Contributions': [
                'Co-authored and reviewed research content',
                'Presented findings with team',
                'Explored future improvements for VVAs',
                'Strengthened academic research skills'
            ]
        },
        links: [
            { text: 'Read Paper', url: '#' }
        ]
    },

    'MUN Leadership': {
        rating: '2025',
        title: 'Model United Nations – Head of Technology',
        description: 'Led the digital and technical operations of the MUN team, ensuring smooth event execution and effective technical integration.',
        sections: {
            'Leadership Responsibilities': [
                'Oversaw all digital tools and platforms for event management',
                'Coordinated a team for technical support during conferences',
                'Managed communication systems and online delegate resources',
                'Developed guidelines for digital infrastructure'
            ],
            'Key Achievements': [
                'Ensured seamless technical execution for 300+ delegates',
                'Introduced digital registration and scheduling system',
                'Enhanced conference experience with improved IT solutions',
                'Recognized for leadership and problem-solving under pressure'
            ]
        },
        links: [
            { text: 'Event Website', url: 'https://gcs-mun.vercel.app' },
            { text: 'Leadership Recognition', url: '#' }
        ]
    },

    'Development Tools': {
        rating: 'Tools',
        title: 'Development Tools',
        description: 'Experience with modern development environments, debugging utilities, and version control workflows to streamline coding and collaboration.',
        sections: {
            'Core Tools': [
                'Git and GitHub workflows',
                'VS Code with productivity extensions',
                'Integrated terminal and build tools'
            ],
            'Debugging & Testing': [
                'Debugging with breakpoints and logs',
                'Unit and integration testing',
                'Automated testing frameworks',
                'Error handling and profiling tools'
            ],
            'Workflow & Optimization': [
                'Branching strategies for collaboration',
                'Code reviews and pull requests',
                'Performance profiling and optimization',
                'Continuous improvement practices'
            ]
        },
        links: [
            { text: 'View Setup', url: '#' }
        ]
    },

    'APIs & Services': {
        rating: 'Integration',
        title: 'APIs & Services',
        description: 'Hands-on experience designing, building, and integrating APIs for seamless data exchange and service interaction across applications.',
        sections: {
            'Core Skills': [
                'REST API design and implementation',
                'Flask and Django-based endpoints',
                'JSON and XML data handling',
                'Authentication and authorization in APIs'
            ],
            'Integrations': [
                'Currency conversion API in Finance Tracker',
                'Third-party data imports and exports',
                'Excel/CSV integration using Pandas',
                'External library and service integration'
            ],
            'Best Practices': [
                'Error handling and validation',
                'Secure API communication',
                'Documentation for API usage',
                'Testing endpoints with Postman and Pytest'
            ]
        },
        links: [
            { text: 'View Finance Tracker', url: '#' }
        ]
    },

    'Continuous Learning': {
        rating: 'Learning',
        title: 'Continuous Learning',
        description: 'Currently exploring React, ML, and advanced system design patterns. Always experimenting with emerging technologies and frameworks.',
        sections: {
            'Current Learning': [
                'React and modern frontend frameworks',
                'Machine Learning fundamentals',
                'System design principles',
                'Cloud computing and DevOps'
            ]
        },
        links: []
    },

    'Algorithm Challenges': {
        rating: 'Code',
        title: 'Algorithm Challenges',
        description: 'Active on LeetCode with focus on optimization and clean, readable code practices.',
        sections: {
            'Skills': [
                'Problem-solving and algorithmic thinking',
                'Code optimization techniques',
                'Data structure implementation'
            ]
        },
        links: []
    },

    'Coming Soon': {
        rating: '',
        title: 'Coming Soon!',
        description: 'Exciting new projects are on the way. Stay tuned for upcoming releases!',
        sections: {
            'What to Expect': [
                'Innovative coding projects',
                'More advanced web applications',
                'Cutting-edge AI tools',
                'Open-source contributions'
            ]
        },
        links: [
            { text: 'Check Back Later', url: '#' }
        ]
    }
};

// Normalize function for matching card titles
function normalizeKey(s) {
    return String(s || '').toLowerCase().replace(/\s+/g, ' ').trim().replace(/[^a-z0-9&]+/g, '');
}

// Create key mappings
const keyMap = {};
Object.keys(cardData).forEach(k => {
    keyMap[normalizeKey(k)] = k;
    const t = cardData[k].title || k;
    keyMap[normalizeKey(t)] = k;
});

// Create modal HTML
function createModal() {
    const modalHTML = `
        <div id="cardModal" class="modal-overlay">
            <div class="modal-content">
                <button class="modal-close">&times;</button>
                <div class="modal-header">
                    <div class="modal-rating"></div>
                    <h2 class="modal-title"></h2>
                </div>
                <div class="modal-body">
                    <p class="modal-description"></p>
                    <div class="modal-sections"></div>
                    <div class="modal-links"></div>
                </div>
            </div>
        </div>
    `;
    
    if (!document.getElementById('cardModal')) {
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
}

// Open modal
function openModal(key) {
    const modal = document.getElementById('cardModal');
    const data = cardData[key];
    
    if (!modal || !data) {
        console.warn('Modal data not found for key:', key);
        return;
    }

    modal.querySelector('.modal-rating').textContent = data.rating || '';
    modal.querySelector('.modal-title').textContent = data.title || key;
    modal.querySelector('.modal-description').textContent = data.description || '';
    
    // Add sections
    const sectionsContainer = modal.querySelector('.modal-sections');
    sectionsContainer.innerHTML = '';
    Object.entries(data.sections || {}).forEach(([sectionTitle, items]) => {
        const sectionHTML = `
            <div class="modal-section">
                <h3>${sectionTitle}</h3>
                <ul>
                    ${Array.isArray(items) ? items.map(item => `<li>${item}</li>`).join('') : `<li>${items}</li>`}
                </ul>
            </div>
        `;
        sectionsContainer.insertAdjacentHTML('beforeend', sectionHTML);
    });

    // Add links
    const linksContainer = modal.querySelector('.modal-links');
    linksContainer.innerHTML = '';
    (data.links || []).forEach(link => {
        linksContainer.insertAdjacentHTML('beforeend', 
            `<a href="${link.url}" class="modal-button" target="_blank" rel="noopener noreferrer">${link.text}</a>`);
    });

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Close modal
function closeModal() {
    const modal = document.getElementById('cardModal');
    if (!modal) return;
    
    modal.classList.remove('active');
    document.body.style.overflow = 'auto';
}

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Portfolio loaded');
    
    // Create modal
    createModal();
    
    // Add click handlers for movie cards
    document.addEventListener('click', function(e) {
        const card = e.target.closest('.movie-card');
        if (card) {
            const title = card.querySelector('.movie-title')?.textContent?.trim();
            if (title) {
                const mapped = keyMap[normalizeKey(title)];
                if (mapped) {
                    console.log('Opening modal for:', title);
                    openModal(mapped);
                } else {
                    console.warn('No data found for:', title);
                }
            }
        }
        
        // Close modal
        if (e.target.classList.contains('modal-overlay') || e.target.classList.contains('modal-close')) {
            closeModal();
        }
    });
    
    // Add keyboard handler
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
    
    // Add scroll button handlers
    document.querySelectorAll('.scroll-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const container = this.parentElement;
            const moviesRow = container.querySelector('.movies-row');
            const cardWidth = 295;
            
            if (!moviesRow) return;
            
            if (this.classList.contains('left')) {
                moviesRow.scrollBy({ left: -cardWidth * 2, behavior: 'smooth' });
            } else {
                moviesRow.scrollBy({ left: cardWidth * 2, behavior: 'smooth' });
            }
        });
    });
    
    console.log('All handlers initialized');
});