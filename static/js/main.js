// Main JavaScript for AutoCad_Buddy Website

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Menu Toggle
    const mobileMenuButton = document.querySelector('.mobile-menu');
    const navLinks = document.querySelector('.nav-links');
    
    if (mobileMenuButton) {
        mobileMenuButton.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }
    
    // Smooth Scrolling for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
                
                // Close mobile menu if open
                if (navLinks.classList.contains('active')) {
                    navLinks.classList.remove('active');
                }
            }
        });
    });
    
    // Fade-in Animation on Scroll
    const fadeElements = document.querySelectorAll('.fade-in');
    
    function checkFade() {
        fadeElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;
            
            if (elementTop < window.innerHeight - elementVisible) {
                element.classList.add('active');
            }
        });
    }
    
    // Run on initial load
    checkFade();
    
    // Run on scroll
    window.addEventListener('scroll', checkFade);
    
    // Demo File Upload Simulation
    const fileUploadArea = document.querySelector('.file-upload-area');
    if (fileUploadArea) {
        fileUploadArea.addEventListener('click', function() {
            alert('This is a demo. In the actual application, you would be able to upload your 2D files here.');
        });
    }
    
    // Testimonial Slider
    let currentTestimonial = 0;
    const testimonials = [
        {
            text: "AutoCad_Buddy has revolutionized our workflow. What used to take us hours of manual modeling now happens in minutes. The accuracy is impressive, and our clients love the interactive 3D models we can share with them.",
            author: "Sarah Chen",
            role: "Senior Architectural Designer"
        },
        {
            text: "As a kitchen designer, I need to quickly show clients how their space will look. AutoCad_Buddy not only converts my 2D drawings to 3D, but also helps me find the right appliances based on my client's location. It's a game-changer!",
            author: "Michael Rodriguez",
            role: "Kitchen Design Consultant"
        },
        {
            text: "I was skeptical at first, but AutoCad_Buddy exceeded my expectations. The dimension accuracy is spot-on, and the web-based sharing makes it easy to collaborate with my team and clients. Well worth the investment.",
            author: "Jamal Washington",
            role: "Restaurant Owner"
        }
    ];
    
    const testimonialContainer = document.querySelector('.testimonial');
    
    if (testimonialContainer && testimonials.length > 1) {
        // Create navigation dots
        const dotsContainer = document.createElement('div');
        dotsContainer.className = 'testimonial-dots';
        testimonialContainer.parentNode.appendChild(dotsContainer);
        
        // Add dots for each testimonial
        testimonials.forEach((_, index) => {
            const dot = document.createElement('span');
            dot.className = 'testimonial-dot';
            if (index === 0) dot.classList.add('active');
            dot.addEventListener('click', () => {
                showTestimonial(index);
            });
            dotsContainer.appendChild(dot);
        });
        
        // Function to show testimonial
        function showTestimonial(index) {
            const testimonial = testimonials[index];
            testimonialContainer.innerHTML = `
                <div class="testimonial-text">${testimonial.text}</div>
                <div class="testimonial-author">${testimonial.author}</div>
                <div class="testimonial-role">${testimonial.role}</div>
            `;
            
            // Update active dot
            document.querySelectorAll('.testimonial-dot').forEach((dot, i) => {
                if (i === index) {
                    dot.classList.add('active');
                } else {
                    dot.classList.remove('active');
                }
            });
            
            currentTestimonial = index;
        }
        
        // Auto-rotate testimonials
        setInterval(() => {
            currentTestimonial = (currentTestimonial + 1) % testimonials.length;
            showTestimonial(currentTestimonial);
        }, 5000);
    }
    
    // Pricing Toggle (Monthly/Annual)
    const pricingToggle = document.getElementById('pricing-toggle');
    const monthlyPrices = document.querySelectorAll('.monthly-price');
    const annualPrices = document.querySelectorAll('.annual-price');
    
    if (pricingToggle) {
        pricingToggle.addEventListener('change', function() {
            if (this.checked) {
                // Show annual prices
                monthlyPrices.forEach(el => el.style.display = 'none');
                annualPrices.forEach(el => el.style.display = 'block');
            } else {
                // Show monthly prices
                monthlyPrices.forEach(el => el.style.display = 'block');
                annualPrices.forEach(el => el.style.display = 'none');
            }
        });
    }
    
    // Form Validation
    const contactForm = document.getElementById('contact-form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Simple validation
            let valid = true;
            const nameInput = document.getElementById('name');
            const emailInput = document.getElementById('email');
            const messageInput = document.getElementById('message');
            
            if (nameInput && nameInput.value.trim() === '') {
                valid = false;
                nameInput.classList.add('error');
            } else if (nameInput) {
                nameInput.classList.remove('error');
            }
            
            if (emailInput) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(emailInput.value.trim())) {
                    valid = false;
                    emailInput.classList.add('error');
                } else {
                    emailInput.classList.remove('error');
                }
            }
            
            if (messageInput && messageInput.value.trim() === '') {
                valid = false;
                messageInput.classList.add('error');
            } else if (messageInput) {
                messageInput.classList.remove('error');
            }
            
            if (valid) {
                // In a real application, this would submit the form
                alert('Thank you for your message! We will get back to you soon.');
                contactForm.reset();
            } else {
                alert('Please fill out all required fields correctly.');
            }
        });
    }
});
