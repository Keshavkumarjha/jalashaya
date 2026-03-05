/* ================================================================
   JALASHAYA – Shared JavaScript
   ================================================================ */

/* ── Cursor ─────────────────────────────────────────────────── */
const dot  = document.getElementById('cursorDot');
const ring = document.getElementById('cursorRing');
if (dot && ring) {
  let rx = 0, ry = 0, dx = 0, dy = 0;
  document.addEventListener('mousemove', e => {
    dx = e.clientX; dy = e.clientY;
    dot.style.left = dx + 'px';
    dot.style.top  = dy + 'px';
  });
  (function animRing() {
    rx += (dx - rx) * 0.15;
    ry += (dy - ry) * 0.15;
    ring.style.left = rx + 'px';
    ring.style.top  = ry + 'px';
    requestAnimationFrame(animRing);
  })();
  document.querySelectorAll('a, button, .btn, input, textarea, select, .feature-card, .prod-card, .product-card').forEach(el => {
    el.addEventListener('mouseenter', () => ring.classList.add('hovered'));
    el.addEventListener('mouseleave', () => ring.classList.remove('hovered'));
  });
}

/* ── Navbar scroll ───────────────────────────────────────────── */
const navbar = document.getElementById('navbar');
if (navbar) {
  window.addEventListener('scroll', () => navbar.classList.toggle('scrolled', window.scrollY > 30));
}

/* ── Mobile menu ─────────────────────────────────────────────── */
const toggle   = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');
if (toggle && navLinks) {
  toggle.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    const spans = toggle.querySelectorAll('span');
    const open  = navLinks.classList.contains('open');
    spans[0].style.transform = open ? 'rotate(45deg) translate(5px,5px)'  : '';
    spans[1].style.transform = open ? 'scaleX(0)'                          : '';
    spans[2].style.transform = open ? 'rotate(-45deg) translate(5px,-5px)' : '';
  });
}

/* ── Reveal on scroll ────────────────────────────────────────── */
const revealObs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); revealObs.unobserve(e.target); }
  });
}, { threshold: 0.1 });
document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

/* ── Water canvas ────────────────────────────────────────────── */
const canvas = document.getElementById('water-canvas');
if (canvas) {
  const ctx = canvas.getContext('2d');
  let W, H, time = 0;
  const resize = () => { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; };
  resize();
  window.addEventListener('resize', resize);
  (function draw() {
    ctx.clearRect(0, 0, W, H);
    for (let i = 0; i < 5; i++) {
      ctx.beginPath();
      const amp   = 25 + i * 8;
      const freq  = 0.006 - i * 0.0005;
      const speed = 0.3 + i * 0.1;
      const yBase = H * (0.3 + i * 0.15);
      ctx.moveTo(0, yBase);
      for (let x = 0; x <= W; x += 3) {
        const y = yBase
          + Math.sin(x * freq + time * speed) * amp
          + Math.sin(x * freq * 2.1 + time * speed * 0.7) * amp * 0.4;
        ctx.lineTo(x, y);
      }
      ctx.lineTo(W, H); ctx.lineTo(0, H); ctx.closePath();
      const grad = ctx.createLinearGradient(0, yBase - amp, 0, H);
      grad.addColorStop(0, `rgba(0,180,216,${0.08 - i * 0.01})`);
      grad.addColorStop(1, `rgba(10,30,60,0.02)`);
      ctx.fillStyle = grad;
      ctx.fill();
    }
    time += 0.01;
    requestAnimationFrame(draw);
  })();
}

/* ── Toast auto-dismiss ──────────────────────────────────────── */
setTimeout(() => {
  document.querySelectorAll('.message-toast').forEach(t => {
    t.style.transition = 'opacity 0.5s, transform 0.5s';
    t.style.opacity = '0';
    t.style.transform = 'translateX(40px)';
    setTimeout(() => t.remove(), 500);
  });
}, 4000);

/* ── FAQ accordion ───────────────────────────────────────────── */
document.querySelectorAll('.faq-trigger').forEach(btn => {
  btn.addEventListener('click', () => {
    const item   = btn.closest('.faq-item');
    const isOpen = item.classList.contains('open');
    document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
    if (!isOpen) item.classList.add('open');
  });
});

/* ── Password toggle (multiple) ─────────────────────────────── */
document.querySelectorAll('[data-pw-toggle]').forEach(btn => {
  btn.addEventListener('click', () => {
    const target = document.getElementById(btn.dataset.pwToggle);
    if (!target) return;
    const isText = target.type === 'text';
    target.type  = isText ? 'password' : 'text';
    btn.innerHTML = isText ? '<i class="fas fa-eye"></i>' : '<i class="fas fa-eye-slash"></i>';
  });
});

/* ── Password strength ───────────────────────────────────────── */
const pw1 = document.getElementById('id_password1');
if (pw1) {
  const segs  = [1, 2, 3, 4].map(i => document.getElementById('seg' + i));
  const label = document.getElementById('strengthText');
  const levels = [
    { color: '#ff6b6b', text: 'Too short' },
    { color: '#ffa94d', text: 'Weak' },
    { color: '#ffe066', text: 'Fair' },
    { color: '#69db7c', text: 'Good' },
    { color: '#40c057', text: 'Strong' },
  ];
  function calcStrength(pw) {
    let s = 0;
    if (pw.length >= 8)  s++;
    if (pw.length >= 12) s++;
    if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
    if (/[0-9]/.test(pw))    s++;
    if (/[^A-Za-z0-9]/.test(pw)) s++;
    return Math.min(s, 4);
  }
  pw1.addEventListener('input', () => {
    const score = pw1.value.length === 0 ? -1 : calcStrength(pw1.value);
    if (segs[0]) segs.forEach((seg, i) => {
      seg.style.background = score >= 0 && i <= score - 1 ? levels[score].color : 'rgba(255,255,255,0.08)';
    });
    if (label) { label.textContent = score >= 0 ? levels[score].text : ''; label.style.color = score >= 0 ? levels[score].color : 'var(--muted)'; }
  });
}

/* ── Counter animation ───────────────────────────────────────── */
document.querySelectorAll('[data-counter]').forEach(el => {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const raw    = el.textContent;
      const num    = parseFloat(raw.replace(/[^0-9.]/g, ''));
      const suffix = raw.replace(/[\d.,]/g, '').trim();
      let start    = null;
      const step   = ts => {
        if (!start) start = ts;
        const p    = Math.min((ts - start) / 2000, 1);
        const ease = 1 - Math.pow(1 - p, 3);
        el.textContent = (ease * num).toFixed(num < 10 ? 1 : 0) + suffix;
        if (p < 1) requestAnimationFrame(step); else el.textContent = raw;
      };
      requestAnimationFrame(step);
      obs.unobserve(el);
    });
  }, { threshold: 0.5 });
  obs.observe(el);
});

/* ── Product filter tabs ─────────────────────────────────────── */
document.querySelectorAll('.filter-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const filter = tab.dataset.filter;
    document.querySelectorAll('.prod-card[data-cat]').forEach(card => {
      const show = filter === 'all' || card.dataset.cat === filter;
      card.style.transition = 'all 0.4s cubic-bezier(0.23,1,0.32,1)';
      card.style.opacity        = show ? '1' : '0.2';
      card.style.transform      = show ? ''  : 'scale(0.95)';
      card.style.pointerEvents  = show ? ''  : 'none';
    });
  });
});

/* ── Add to cart feedback ────────────────────────────────────── */
window.addToCart = function(btn) {
  btn.classList.add('added');
  btn.innerHTML = '<i class="fas fa-check"></i> Added!';
  setTimeout(() => {
    btn.classList.remove('added');
    btn.innerHTML = '<i class="fas fa-shopping-cart"></i> Add';
  }, 2000);
};

/* ── Wishlist toggle ─────────────────────────────────────────── */
window.toggleWishlist = function(btn) { btn.classList.toggle('active'); };

/* ── File upload display ─────────────────────────────────────── */
const fileInput = document.getElementById('attachment');
const fileLabel = document.getElementById('file-name');
if (fileInput && fileLabel) {
  fileInput.addEventListener('change', function() {
    if (this.files[0]) fileLabel.textContent = '📎 ' + this.files[0].name;
  });
}

/* ── Form submit spinner ─────────────────────────────────────── */
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', function() {
    const btn = this.querySelector('.btn-submit');
    if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending…'; btn.style.pointerEvents = 'none'; }
  });
});

/* ── Booking modal ───────────────────────────────────────────── */
const bookingModal = document.getElementById('bookingModal');
if (bookingModal) {
  const bookingForm = document.getElementById('bookingForm');
  const summaryModal = document.getElementById('orderSummaryModal');
  const summaryContent = document.getElementById('orderSummaryContent');
  const confirmOrderSubmit = document.getElementById('confirmOrderSubmit');

  const productIdInput = document.getElementById('bookingProductId');
  const productNameLabel = document.getElementById('bookingProductName');
  const quantityInput = document.getElementById('id_quantity');
  const emailInput = document.getElementById('id_customer_email');
  const addressSelect = document.getElementById('id_selected_address');
  const hiddenDeliveryAddress = document.getElementById('id_delivery_address');
  const savedAddressGroup = document.getElementById('savedAddressGroup');

  const addrLine1 = document.getElementById('id_address_line_1');
  const addrLine2 = document.getElementById('id_address_line_2');
  const addrLandmark = document.getElementById('id_landmark');
  const addrCity = document.getElementById('id_city');
  const addrState = document.getElementById('id_state_name');
  const addrPin = document.getElementById('id_postal_code');
  const addrCountry = document.getElementById('id_country');

  function composeAddressFromInputs() {
    const parts = [
      addrLine1?.value.trim(),
      addrLine2?.value.trim(),
      addrLandmark?.value.trim(),
      addrCity?.value.trim(),
      addrState?.value.trim(),
      addrPin?.value.trim(),
      addrCountry?.value.trim(),
    ].filter(Boolean);
    return parts.join(', ');
  }

  function syncHiddenDeliveryAddress() {
    if (!hiddenDeliveryAddress) return;
    const selected = addressSelect && addressSelect.selectedIndex > 0 ? addressSelect.options[addressSelect.selectedIndex] : null;
    if (selected && selected.dataset.address) {
      hiddenDeliveryAddress.value = selected.dataset.address;
      return;
    }
    hiddenDeliveryAddress.value = composeAddressFromInputs();
  }

  function loadSavedAddresses() {
    if (!emailInput || !addressSelect || !savedAddressGroup) return;
    const email = emailInput.value.trim();
    if (!email) {
      savedAddressGroup.style.display = 'none';
      return;
    }

    fetch(`/ajax/customer-addresses/?email=${encodeURIComponent(email)}`)
      .then(res => res.json())
      .then(data => {
        addressSelect.innerHTML = '<option value="">Add New Address</option>';
        if (data.results && data.results.length) {
          data.results.forEach(item => {
            const option = document.createElement('option');
            option.value = item.id;
            option.textContent = `${item.label}: ${item.address}`;
            option.dataset.address = item.address;
            addressSelect.appendChild(option);
          });
          savedAddressGroup.style.display = 'block';
        } else {
          savedAddressGroup.style.display = 'none';
        }
        syncHiddenDeliveryAddress();
      })
      .catch(() => {
        savedAddressGroup.style.display = 'none';
      });
  }

  document.querySelectorAll('.booking-trigger').forEach(btn => {
    btn.addEventListener('click', () => {
      if (productIdInput) productIdInput.value = btn.dataset.productId || '';
      if (productNameLabel) productNameLabel.textContent = btn.dataset.productName || 'Selected product';
      if (bookingForm) bookingForm.dataset.productPrice = btn.dataset.productPrice || '0';
      bookingModal.classList.add('is-open');
      bookingModal.setAttribute('aria-hidden', 'false');
      loadSavedAddresses();
    });
  });

  if (emailInput) emailInput.addEventListener('blur', loadSavedAddresses);

  [addrLine1, addrLine2, addrLandmark, addrCity, addrState, addrPin, addrCountry].forEach(el => {
    if (el) el.addEventListener('input', syncHiddenDeliveryAddress);
  });

  if (addressSelect) {
    addressSelect.addEventListener('change', syncHiddenDeliveryAddress);
  }

  bookingModal.querySelectorAll('[data-qty-action]').forEach(btn => {
    btn.addEventListener('click', () => {
      if (!quantityInput) return;
      const current = parseInt(quantityInput.value || '1', 10);
      quantityInput.value = String(btn.dataset.qtyAction === 'minus' ? Math.max(1, current - 1) : current + 1);
    });
  });

  bookingModal.querySelectorAll('[data-close-booking]').forEach(el => {
    el.addEventListener('click', () => {
      bookingModal.classList.remove('is-open');
      bookingModal.setAttribute('aria-hidden', 'true');
    });
  });

  if (bookingForm && summaryModal && summaryContent && confirmOrderSubmit) {
    bookingForm.addEventListener('submit', e => {
      if (bookingForm.dataset.confirmed === 'true') return;
      e.preventDefault();
      e.stopImmediatePropagation();
      syncHiddenDeliveryAddress();

      const quantity = parseInt(quantityInput?.value || '1', 10);
      const price = parseFloat(bookingForm.dataset.productPrice || '0');
      const subtotal = quantity * price;
      const delivery = subtotal >= 200 ? 0 : 20;
      const total = subtotal + delivery;

      summaryContent.innerHTML = `
        <div class="summary-row"><strong>Product:</strong><span>${productNameLabel?.textContent || '-'}</span></div>
        <div class="summary-row"><strong>Customer:</strong><span>${document.getElementById('id_customer_name')?.value || '-'}</span></div>
        <div class="summary-row"><strong>Email:</strong><span>${emailInput?.value || '-'}</span></div>
        <div class="summary-row"><strong>Mobile:</strong><span>${document.getElementById('id_customer_mobile')?.value || '-'}</span></div>
        <div class="summary-row"><strong>Quantity:</strong><span>${quantity}</span></div>
        <div class="summary-row"><strong>Delivery Address:</strong><span>${hiddenDeliveryAddress?.value || '-'}</span></div>
        <div class="summary-row"><strong>Subtotal:</strong><span>₹${subtotal.toFixed(2)}</span></div>
        <div class="summary-row"><strong>Delivery Fee:</strong><span>₹${delivery.toFixed(2)}</span></div>
        <div class="summary-row summary-total"><strong>Total:</strong><span>₹${total.toFixed(2)}</span></div>
      `;
      summaryModal.classList.add('is-open');
      summaryModal.setAttribute('aria-hidden', 'false');
    });

    confirmOrderSubmit.addEventListener('click', () => {
      bookingForm.dataset.confirmed = 'true';
      summaryModal.classList.remove('is-open');
      summaryModal.setAttribute('aria-hidden', 'true');
      bookingForm.submit();
    });

    summaryModal.querySelectorAll('[data-close-summary]').forEach(el => {
      el.addEventListener('click', () => {
        summaryModal.classList.remove('is-open');
        summaryModal.setAttribute('aria-hidden', 'true');
      });
    });
  }
}
