const outreachItems = document.querySelectorAll(".outreach-content");

outreachItems.forEach(item => {
    item.addEventListener("mouseenter", () => {
        item.classList.add("is-open");
    });

    item.addEventListener("mouseleave", () => {
        item.classList.remove("is-open");
    });
});


function showSidebar() {
    const sidebar = document.querySelector(".sidebar");
    sidebar.classList.add("open");
}

function hideSidebar() {
    const sidebar = document.querySelector(".sidebar");
    sidebar.classList.remove("open");
}

// Close sidebar when clicking outside
document.addEventListener("click", (e) => {
    const sidebar = document.querySelector(".sidebar");
    const menuIcon = document.querySelector(".menu-icon");
    if (!sidebar.contains(e.target) && !menuIcon.contains(e.target)) {
        sidebar.classList.remove("open");
    }
});

// Close sidebar when clicking a sidebar link
document.querySelectorAll(".sidebar a").forEach(link => {
    link.addEventListener("click", () => {
        document.querySelector(".sidebar").classList.remove("open");
    });
});

// ===== SCROLL-TRIGGERED FADE-IN ANIMATIONS =====
// Add animate-on-scroll class to elements
document.addEventListener("DOMContentLoaded", () => {
    // Select elements to animate
    const animatableElements = [
        ...document.querySelectorAll(".section-title"),
        ...document.querySelectorAll(".publication-card"),
        ...document.querySelectorAll(".outreach-item"),
        ...document.querySelectorAll(".research-focus > div"),
        ...document.querySelectorAll(".contact-title"),
        ...document.querySelectorAll(".simple-contact-links")
    ];
    
    // Add the animation class to all selected elements
    animatableElements.forEach(el => {
        el.classList.add("animate-on-scroll");
    });
    
    // Create Intersection Observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
                observer.unobserve(entry.target); // Only animate once
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: "0px 0px -50px 0px"
    });
    
    // Observe all animatable elements
    animatableElements.forEach(el => observer.observe(el));
});

var prevScrollpos = window.pageYOffset;
window.onscroll = function() {
var currentScrollPos = window.pageYOffset;
  if (prevScrollpos > currentScrollPos) {
    document.getElementById("navbar").style.top = "0";
  } else {
    document.getElementById("navbar").style.top = "-100px";
  }
  prevScrollpos = currentScrollPos;
}

// Scroll research carousel to middle card on mobile
function scrollResearchToMiddle() {
    if (window.innerWidth <= 1028) {
        var rf = document.querySelector(".research-focus");
        if (rf) {
            rf.scrollTo({ left: window.innerWidth * 0.6, behavior: "smooth" });
        }
    }
}

window.addEventListener("load", scrollResearchToMiddle);

// Snap back to middle after user stops interacting with the carousel
(function () {
    var rf = document.querySelector(".research-focus");
    if (!rf) return;
    var snapTimer;
    rf.addEventListener("scrollend", function () {
        clearTimeout(snapTimer);
        snapTimer = setTimeout(scrollResearchToMiddle, 1500);
    });
    // Fallback for browsers without scrollend
    rf.addEventListener("scroll", function () {
        clearTimeout(snapTimer);
        snapTimer = setTimeout(scrollResearchToMiddle, 1500);
    });
})();