import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity, AlertTriangle, ArrowRight, Bell, Check, ChevronDown, CircleHelp,
  CalendarDays, ClipboardCheck, Clock3, FileText, LayoutDashboard, LogOut, Menu, Package, Plus, QrCode, Search, Settings,
  ShieldCheck, Sparkles, TrendingUp, UploadCloud, X,
} from "lucide-react";
import {
  createUserWithEmailAndPassword, onAuthStateChanged, sendPasswordResetEmail,
  signInWithEmailAndPassword, signOut, updateProfile,
} from "@firebase/auth";
import { api, apiBlob } from "./api";
import { auth, isFirebaseConfigured } from "./firebase";

const blankProduct = {
  productName: "", brand: "", category: "Electronics", modelNumber: "", serialNumber: "",
  purchaseDate: new Date().toISOString().slice(0, 10), warrantyDuration: 12,
  purchasePrice: 0, seller: "", notes: "",
};

const money = (value) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value || 0);
const shortDate = (value) => value ? new Date(`${value}T00:00:00`).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "—";

function App() {
  const [user, setUser] = useState(undefined);
  const [authMode, setAuthMode] = useState("login");
  const [authBusy, setAuthBusy] = useState(false);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    if (!auth) {
      setUser(null);
      return undefined;
    }
    return onAuthStateChanged(auth, setUser);
  }, []);

  if (user === undefined) return <div className="boot-screen"><div className="brand-mark"><ShieldCheck size={22} /></div><span>Loading your workspace…</span></div>;
  if (!user) {
    return <AuthScreen mode={authMode} setMode={setAuthMode} busy={authBusy} error={authError} setError={setAuthError}
      onSubmit={async (values) => {
        setAuthError("");
        setAuthBusy(true);
        try {
          if (values.mode === "reset") {
            await sendPasswordResetEmail(auth, values.email);
            setAuthError("Password reset email sent. Check your inbox.");
          } else if (values.mode === "register") {
            const credential = await createUserWithEmailAndPassword(auth, values.email, values.password);
            await updateProfile(credential.user, { displayName: values.name.trim() });
          } else {
            await signInWithEmailAndPassword(auth, values.email, values.password);
          }
        } catch (error) {
          setAuthError(error.message.replace("Firebase: ", ""));
        } finally {
          setAuthBusy(false);
        }
      }} />;
  }
  return <Workspace user={user} onLogout={() => signOut(auth)} />;
}

function AuthScreen({ mode, setMode, busy, error, setError, onSubmit }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const isRegister = mode === "register";
  return (
    <main className="auth-page">
      <div className="auth-art">
        <div className="auth-art-top"><Brand /><span className="secure-label"><ShieldCheck size={14} /> Private by design</span></div>
        <div className="art-copy">
          <div className="eyebrow"><Sparkles size={14} /> YOUR THINGS, TAKEN CARE OF</div>
          <h1>Every warranty.<br /><span>Right where you need it.</span></h1>
          <p>One calm place for product details, invoices, and the dates you don't want to miss.</p>
        </div>
        <div className="art-card">
          <div className="art-card-icon"><Clock3 size={18} /></div>
          <div><small>WARRANTY REMINDER</small><strong>Your MacBook Air expires in 30 days</strong></div>
          <span className="art-dot" />
        </div>
        <div className="auth-art-footer">Built for the things you rely on.</div>
      </div>
      <section className="auth-form-side">
        <div className="mobile-brand"><Brand /></div>
        <form className="auth-form" onSubmit={(event) => {
          event.preventDefault();
          const form = event.currentTarget;
          if (isRegister && password !== form.confirmPassword.value) {
            setError("Passwords do not match.");
            return;
          }
          onSubmit({ mode, name, email, password });
        }}>
          <div className="auth-heading">
            <div className="eyebrow muted-eyebrow">{mode === "reset" ? "ACCOUNT RECOVERY" : "WELCOME TO WARRANTLY"}</div>
            <h2>{mode === "register" ? "Create your account" : mode === "reset" ? "Reset your password" : "Welcome back"}</h2>
            <p>{mode === "register" ? "Start keeping everything in its place." : mode === "reset" ? "We'll send you a link to reset your password." : "Sign in to pick up right where you left off."}</p>
          </div>
          {isRegister && <label>Your name<input value={name} onChange={(e) => setName(e.target.value)} placeholder="Alex Morgan" required autoComplete="name" /></label>}
          <label>Email address<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required autoComplete="email" /></label>
          {mode !== "reset" && <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" minLength="6" required autoComplete={isRegister ? "new-password" : "current-password"} /></label>}
          {isRegister && <label>Confirm password<input name="confirmPassword" type="password" placeholder="Enter your password again" minLength="6" required autoComplete="new-password" /></label>}
          {error && <div className={error.startsWith("Password reset") ? "inline-success" : "inline-error"}>{error}</div>}
              {!isFirebaseConfigured && <div className="config-notice">Add your Firebase web app settings to <code>.env</code> (see <code>.env.example</code>) to enable secure sign-in.</div>}
          {mode === "login" && <button className="text-button forgot-link" type="button" onClick={() => { setError(""); setMode("reset"); }}>Forgot password?</button>}
          <button className="primary-button auth-submit" disabled={busy || !isFirebaseConfigured}>{busy ? "Please wait…" : mode === "register" ? "Create account" : mode === "reset" ? "Send reset link" : "Sign in"}<ArrowRight size={17} /></button>
          <div className="auth-switch">{mode === "register" ? "Already have an account?" : mode === "reset" ? "Remembered your password?" : "New to Warrantly?"}
            <button type="button" className="text-button" onClick={() => { setError(""); setMode(mode === "register" || mode === "reset" ? "login" : "register"); }}>{mode === "register" || mode === "reset" ? "Sign in" : "Create an account"}</button>
          </div>
          <div className="auth-privacy"><ShieldCheck size={15} /> Your account is protected with Firebase Authentication.</div>
        </form>
      </section>
    </main>
  );
}

function Brand() {
  return <div className="brand"><div className="brand-mark"><ShieldCheck size={21} strokeWidth={2.2} /></div><span>warrantly<span className="brand-period">.</span></span></div>;
}

function Workspace({ user, onLogout }) {
  const [products, setProducts] = useState([]);
  const [serviceRecords, setServiceRecords] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [claims, setClaims] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState("Overview");
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All categories");
  const [modal, setModal] = useState(null);
  const [toast, setToast] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setLoadError("");
    try {
      const token = await user.getIdToken();
      const [profileData, productData, notificationData, analyticsData, serviceData, claimData, maintenanceData] = await Promise.all([
        api("/api/auth/me", token), api("/api/products", token), api("/api/notifications", token), api("/api/analytics", token), api("/api/services", token), api("/api/claims", token), api("/api/maintenance", token),
      ]);
      setProducts(productData.items);
      setNotifications(notificationData.items);
      setAnalytics(analyticsData);
      setServiceRecords(serviceData.items);
      setClaims(claimData.items);
      setMaintenance(maintenanceData.items);
    } catch (error) {
      setLoadError(error.message);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { loadData(); }, [user.uid]);

  const categories = useMemo(() => ["All categories", ...new Set(products.map((product) => product.category).filter(Boolean))], [products]);
  const visibleProducts = useMemo(() => products.filter((product) => {
    const matchesSearch = `${product.productName} ${product.brand} ${product.category} ${product.modelNumber}`.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = category === "All categories" || product.category === category;
    const matchesView = activeView !== "Expiring soon" || (product.warrantyDaysRemaining >= 0 && product.warrantyDaysRemaining <= 30);
    return matchesSearch && matchesCategory && matchesView;
  }), [products, search, category, activeView]);
  const unreadCount = notifications.filter((item) => !item.read).length;

  const withToken = async (path, options) => api(path, await user.getIdToken(), options);
  const withTokenBlob = async (path) => apiBlob(path, await user.getIdToken());
  const showToast = (message) => { setToast(message); window.setTimeout(() => setToast(""), 3200); };
  const saveProduct = async (values, editing) => {
    const saved = await withToken(editing ? `/api/products/${editing.productId}` : "/api/products", {
      method: editing ? "PUT" : "POST", body: JSON.stringify(values),
    });
    if (modal.file) {
      try {
        const formData = new FormData();
        formData.append("file", modal.file);
        await withToken(`/api/invoices/${saved.productId}`, { method: "POST", body: formData });
      } catch (error) {
        if (!editing) {
          setModal({ type: "product", product: saved, file: null });
          await loadData();
        }
        throw new Error(`Product details were saved, but the invoice upload failed: ${error.message}`);
      }
    }
    setModal(null);
    await loadData();
    showToast(editing ? "Product details updated." : "Product added to your collection.");
  };
  const deleteProduct = async (product) => {
    if (!window.confirm(`Delete ${product.productName} and its service history?`)) return;
    try {
      await withToken(`/api/products/${product.productId}`, { method: "DELETE" });
      await loadData();
      showToast("Product deleted.");
    } catch (error) { setLoadError(error.message); }
  };
  const markRead = async (item) => {
    try {
      await withToken(`/api/notifications/${item.notificationId}/read`, { method: "PATCH" });
      setNotifications((current) => current.map((notice) => notice.notificationId === item.notificationId ? { ...notice, read: true } : notice));
    } catch (error) { setLoadError(error.message); }
  };

  const pageTitle = activeView === "Overview" ? "Overview" : activeView;
  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "sidebar-open" : ""}`}>
        <div className="sidebar-brand"><Brand /><button className="mobile-close icon-button" onClick={() => setSidebarOpen(false)} aria-label="Close menu"><X size={18} /></button></div>
        <div className="workspace-label">WORKSPACE</div>
        <nav className="side-nav">
          <NavButton icon={<LayoutDashboard size={18} />} label="Overview" active={activeView === "Overview"} onClick={() => { setActiveView("Overview"); setSidebarOpen(false); }} />
          <NavButton icon={<Package size={18} />} label="My products" active={activeView === "My products"} count={products.length} onClick={() => { setActiveView("My products"); setSidebarOpen(false); }} />
          <NavButton icon={<Clock3 size={18} />} label="Expiring soon" active={activeView === "Expiring soon"} count={analytics?.expiringWarranties || 0} onClick={() => { setActiveView("Expiring soon"); setSidebarOpen(false); }} />
          <NavButton icon={<Activity size={18} />} label="Service history" active={activeView === "Service history"} onClick={() => { setActiveView("Service history"); setSidebarOpen(false); }} />
          <NavButton icon={<UploadCloud size={18} />} label="Invoice scanner" active={activeView === "Invoice scanner"} onClick={() => { setActiveView("Invoice scanner"); setSidebarOpen(false); }} />
          <NavButton icon={<QrCode size={18} />} label="QR scanner" active={activeView === "QR scanner"} onClick={() => { setActiveView("QR scanner"); setSidebarOpen(false); }} />
          <NavButton icon={<ClipboardCheck size={18} />} label="Warranty claims" active={activeView === "Warranty claims"} onClick={() => { setActiveView("Warranty claims"); setSidebarOpen(false); }} />
          <NavButton icon={<CalendarDays size={18} />} label="Maintenance" active={activeView === "Maintenance"} onClick={() => { setActiveView("Maintenance"); setSidebarOpen(false); }} />
          <NavButton icon={<TrendingUp size={18} />} label="Analytics" active={activeView === "Analytics"} onClick={() => { setActiveView("Analytics"); setSidebarOpen(false); }} />
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-help"><div className="help-icon"><CircleHelp size={17} /></div><div><strong>Need a hand?</strong><span>Your warranties are in good hands.</span></div></div>
          <div className="sidebar-user">
            <div className="avatar">{(user.displayName || user.email || "U").slice(0, 1).toUpperCase()}</div>
            <div className="user-text"><strong>{user.displayName || "Your account"}</strong><span>{user.email}</span></div>
            <button className="icon-button user-more" aria-label="Account options" onClick={() => setProfileOpen(!profileOpen)}><ChevronDown size={16} /></button>
            {profileOpen && <div className="profile-menu"><button onClick={onLogout}><LogOut size={15} /> Sign out</button></div>}
          </div>
        </div>
      </aside>
      {sidebarOpen && <button aria-label="Close navigation" className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} />}
      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" aria-label="Open menu" onClick={() => setSidebarOpen(true)}><Menu size={20} /></button>
          <div className="breadcrumb"><span>Workspace</span><span className="breadcrumb-slash">/</span><strong>{pageTitle}</strong></div>
          <div className="topbar-actions">
            <div className="today-label">{new Date().toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}</div>
            <button className="notification-button" aria-label="Notifications" onClick={() => setModal({ type: "notifications" })}><Bell size={18} />{unreadCount > 0 && <span className="notification-dot" />}</button>
            <div className="topbar-avatar">{(user.displayName || user.email || "U").slice(0, 1).toUpperCase()}</div>
          </div>
        </header>
        <div className="content">
          {loadError && <div className="error-banner"><AlertTriangle size={17} /><span>{loadError}</span><button aria-label="Dismiss error" onClick={() => setLoadError("")}><X size={16} /></button></div>}
          <div className="page-heading">
            <div><div className="eyebrow muted-eyebrow">YOUR PERSONAL INVENTORY</div><h1>{activeView === "Overview" ? `Good ${timeOfDay()}, ${user.displayName?.split(" ")[0] || "there"}` : pageTitle}<span className="heading-period">.</span></h1>
              <p>{activeView === "Overview" ? "Here's what's happening with your warranties." : activeView === "Expiring soon" ? "Stay ahead of the warranties ending soon." : activeView === "Service history" ? "Keep every repair and check-up in one place." : "Everything you own, neatly organized."}</p>
            </div>
            {["Overview", "My products", "Expiring soon"].includes(activeView) && (
              <button className="primary-button add-product-button" onClick={() => setModal({ type: "product", product: null, file: null })}><Plus size={17} /> Add product</button>
            )}
          </div>
          {activeView === "Overview" && <Overview analytics={analytics} products={products} onAdd={() => setModal({ type: "product", product: null, file: null })} onOpenProduct={(product) => setModal({ type: "details", product })} />}
          {activeView === "Invoice scanner" && <InvoiceScanner products={products} withToken={withToken} onSaved={async () => { await loadData(); setActiveView("My products"); }} />}
          {activeView === "QR scanner" && <QrScanner withToken={withToken} onOpen={(product) => setModal({ type: "details", product })} />}
          {activeView === "Warranty claims" && <ClaimsView claims={claims} products={products} withToken={withToken} withTokenBlob={withTokenBlob} onChanged={async () => { await loadData(); }} />}
          {activeView === "Maintenance" && <MaintenanceView records={maintenance} products={products} withToken={withToken} onChanged={async () => { await loadData(); }} />}
          {activeView === "Analytics" && <AnalyticsView analytics={analytics} />}
          {["Overview", "My products", "Expiring soon", "Service history"].includes(activeView) && <section className="products-section">
            {activeView === "Service history" ? <ServiceHistory records={serviceRecords.filter((record) => `${record.productName} ${record.description} ${record.provider}`.toLowerCase().includes(search.toLowerCase()))} loading={loading} search={search} onSearch={setSearch} /> : <>
            <div className="section-heading">
              <div><h2>{activeView === "Overview" ? "Your products" : activeView === "Expiring soon" ? "Expiring warranties" : activeView === "Service history" ? "Products with service records" : "All products"}</h2>
                <p>{visibleProducts.length} {visibleProducts.length === 1 ? "item" : "items"} in your collection</p></div>
              <div className="table-controls">
                <div className="search-field"><Search size={16} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search products..." /></div>
                <div className="select-wrap"><select value={category} onChange={(e) => setCategory(e.target.value)} aria-label="Filter by category">{categories.map((item) => <option key={item}>{item}</option>)}</select><ChevronDown size={15} /></div>
              </div>
            </div>
            <ProductTable products={activeView === "Overview" ? visibleProducts.slice(0, 5) : visibleProducts} loading={loading} onSelect={(product) => setModal({ type: "details", product })} onEdit={(product) => setModal({ type: "product", product, file: null })} onDelete={deleteProduct} />
            {activeView === "Overview" && visibleProducts.length > 5 && <button className="view-all-button" onClick={() => setActiveView("My products")}>View all {visibleProducts.length} products <ArrowRight size={15} /></button>}
            </>}
          </section>}
          <footer className="page-footer"><span>Made for peace of mind.</span><span><ShieldCheck size={14} /> Your data is private and secure</span></footer>
        </div>
      </main>
      {modal?.type === "product" && <ProductModal product={modal.product} file={modal.file} onClose={() => setModal(null)} onSave={saveProduct} onFile={(file) => setModal((current) => ({ ...current, file }))} />}
      {modal?.type === "details" && <DetailsModal product={modal.product} token={user.getIdToken.bind(user)} onClose={() => setModal(null)} onChanged={loadData} onToast={showToast} />}
      {modal?.type === "notifications" && <NotificationsModal items={notifications} onClose={() => setModal(null)} onRead={markRead} />}
      {toast && <div className="toast"><span className="toast-check"><Check size={15} /></span>{toast}</div>}
    </div>
  );
}

function timeOfDay() {
  const hour = new Date().getHours();
  return hour < 12 ? "morning" : hour < 18 ? "afternoon" : "evening";
}

function NavButton({ icon, label, active, count, onClick }) {
  return <button className={`nav-item ${active ? "nav-active" : ""}`} onClick={onClick}>{icon}<span>{label}</span>{count > 0 && <span className="nav-count">{count}</span>}</button>;
}

function Overview({ analytics, products, onAdd, onOpenProduct }) {
  if (!analytics) return <div className="metrics-skeleton" aria-label="Loading analytics"><div /><div /><div /><div /></div>;
  const cards = [
    { label: "Total products", value: analytics.totalProducts, icon: <Package size={17} />, tone: "blue", hint: "in your collection" },
    { label: "Active warranties", value: analytics.activeWarranties, icon: <ShieldCheck size={17} />, tone: "green", hint: "currently covered" },
    { label: "Expiring soon", value: analytics.expiringWarranties, icon: <Clock3 size={17} />, tone: "amber", hint: "within 30 days" },
    { label: "Total spend", value: money(analytics.totalPurchaseSpending), icon: <TrendingUp size={17} />, tone: "purple", hint: "across all purchases" },
  ];
  const urgent = products.filter((item) => item.warrantyDaysRemaining >= 0 && item.warrantyDaysRemaining <= 30).sort((a, b) => a.warrantyDaysRemaining - b.warrantyDaysRemaining).slice(0, 3);
  const maxCategory = Math.max(1, ...(analytics.categories || []).map((item) => item.count));
  return <>
    <div className="metrics-grid">{cards.map((card) => <div className="metric-card" key={card.label}><div className="metric-top"><span>{card.label}</span><span className={`metric-icon ${card.tone}`}>{card.icon}</span></div><strong className="metric-value">{card.value}</strong><span className="metric-hint">{card.hint}</span></div>)}</div>
    <div className="overview-lower">
      <section className="panel expiry-panel"><div className="panel-heading"><div><h3>Coming up</h3><p>Warranties that need your attention</p></div><span className="panel-heading-icon amber-soft"><Clock3 size={17} /></span></div>
        {urgent.length === 0 ? <div className="empty-mini"><div className="empty-check"><Check size={17} /></div><div><strong>All clear for now</strong><span>No warranties expiring in the next 30 days.</span></div></div> : <div className="upcoming-list">{urgent.map((product) => <button className="upcoming-item" key={product.productId} onClick={() => onOpenProduct(product)}><ProductGlyph product={product} /><span className="upcoming-name"><strong>{product.productName}</strong><small>{product.brand || product.category}</small></span><span className={`days-left ${product.warrantyDaysRemaining <= 7 ? "days-urgent" : ""}`}>{product.warrantyDaysRemaining === 0 ? "Today" : `${product.warrantyDaysRemaining} days`}</span></button>)}</div>}
      </section>
      <section className="panel categories-panel"><div className="panel-heading"><div><h3>Your collection</h3><p>A look at your product categories</p></div><span className="panel-heading-icon blue-soft"><Package size={17} /></span></div>
        {analytics.categories?.length ? <div className="category-chart">{analytics.categories.slice(0, 5).map((item, index) => <div className="category-row" key={item.category}><div className="category-label"><span>{item.category}</span><span>{item.count}</span></div><div className="bar-track"><span className={`category-bar bar-${index % 5}`} style={{ width: `${Math.max(7, item.count / maxCategory * 100)}%` }} /></div></div>)}</div> : <div className="category-empty"><div className="category-empty-icon"><Package size={18} /></div><strong>Your collection starts here</strong><span>Add a product to see your breakdown.</span><button className="text-button" onClick={onAdd}>Add your first product <ArrowRight size={14} /></button></div>}
      </section>
    </div>
  </>;
}

function FeatureEmpty({ icon, title, children }) {
  return <section className="feature-page"><div className="feature-card"><div className="feature-card-icon">{icon}</div><h2>{title}</h2>{children}</div></section>;
}

function InvoiceScanner({ withToken, onSaved }) {
  const [file, setFile] = useState(null);
  const [fields, setFields] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");
  const extract = async (selected) => {
    if (!selected) return;
    setFile(selected);
    setProcessing(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", selected);
      const result = await withToken("/api/ocr/extract", { method: "POST", body: form });
      setFields({ productName: "", brand: "", category: "Electronics", modelNumber: "", serialNumber: "", purchaseDate: new Date().toISOString().slice(0, 10), purchasePrice: 0, warrantyDuration: 12, seller: "", notes: "", ...result.fields });
    } catch (exception) {
      setError(exception.message);
      setFields({ ...blankProduct });
    } finally {
      setProcessing(false);
    }
  };
  const setField = (event) => setFields((current) => ({ ...current, [event.target.name]: event.target.value }));
  const save = async () => {
    setProcessing(true);
    setError("");
    try {
      const saved = await withToken("/api/products", { method: "POST", body: JSON.stringify({ ...fields, warrantyDuration: Number(fields.warrantyDuration), purchasePrice: Number(fields.purchasePrice) }) });
      if (file) {
        const form = new FormData();
        form.append("file", file);
        await withToken(`/api/invoices/${saved.productId}`, { method: "POST", body: form });
      }
      await onSaved();
    } catch (exception) { setError(exception.message); }
    finally { setProcessing(false); }
  };
  return <section className="feature-page">
    <div className="scanner-layout">
      <div className="feature-card scanner-upload">
        <div className="feature-card-icon"><UploadCloud size={21} /></div><h2>Scan an invoice</h2><p>Upload a PDF or image, then review every extracted field before saving.</p>
        <label className="drop-zone" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); extract(event.dataTransfer.files?.[0]); }}>
          <UploadCloud size={24} /><strong>{file?.name || "Drop invoice here"}</strong><span>PDF, JPG or PNG · 10 MB maximum</span>
          <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(event) => extract(event.target.files?.[0])} />
        </label>
        {processing && <div className="processing"><span className="spinner" />Processing invoice…</div>}
        {error && <div className="inline-error">{error}</div>}
      </div>
      {fields && <div className="feature-card scanner-form"><div className="section-heading"><div><h2>Extracted details</h2><p>Review and edit before confirmation</p></div></div>
        <div className="form-grid">
          <label className="span-two">Product name *<input name="productName" value={fields.productName} onChange={setField} required /></label>
          <label>Brand<input name="brand" value={fields.brand} onChange={setField} /></label>
          <label>Category<select name="category" value={fields.category} onChange={setField}>{["Electronics","Appliances","Furniture","Tools","Fitness","Other"].map((item)=><option key={item}>{item}</option>)}</select></label>
          <label>Model number<input name="modelNumber" value={fields.modelNumber} onChange={setField} /></label>
          <label>Serial number<input name="serialNumber" value={fields.serialNumber} onChange={setField} /></label>
          <label>Purchase date<input name="purchaseDate" type="date" value={String(fields.purchaseDate).slice(0,10)} onChange={setField} /></label>
          <label>Warranty duration (months)<input name="warrantyDuration" type="number" min="0" value={fields.warrantyDuration} onChange={setField} /></label>
          <label>Purchase price<input name="purchasePrice" type="number" min="0" step="0.01" value={fields.purchasePrice} onChange={setField} /></label>
          <label>Seller<input name="seller" value={fields.seller} onChange={setField} /></label>
        </div>
        <div className="scanner-actions"><button className="secondary-button" onClick={() => setFields(null)}>Clear</button><button className="primary-button" disabled={!fields.productName || processing} onClick={save}>Confirm and save</button></div>
      </div>}
    </div>
  </section>;
}

function QrScanner({ withToken, onOpen }) {
  const [productId, setProductId] = useState("");
  const [error, setError] = useState("");
  const [videoActive, setVideoActive] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const stopCamera = () => { streamRef.current?.getTracks().forEach((track) => track.stop()); streamRef.current = null; setVideoActive(false); };
  const lookup = async (id) => {
    setError("");
    if (!id.trim()) return;
    try { onOpen(await withToken(`/api/qr/scan/${encodeURIComponent(id.trim())}`)); }
    catch (exception) { setError(exception.message); }
  };
  const startCamera = async () => {
    setError("");
    if (!("BarcodeDetector" in window)) { setError("Camera QR detection is not supported by this browser. Enter the product ID shown in the QR URL."); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
      streamRef.current = stream;
      setVideoActive(true);
      await new Promise((resolve) => window.setTimeout(resolve, 50));
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        const detector = new window.BarcodeDetector({ formats: ["qr_code"] });
        const scan = async () => {
          if (!videoRef.current) return;
          try {
            const codes = await detector.detect(videoRef.current);
            if (codes[0]?.rawValue) {
              const match = codes[0].rawValue.match(/\/products\/([^/?#]+)/);
              if (match) { stopCamera(); await lookup(decodeURIComponent(match[1])); return; }
            }
          } catch {}
          window.requestAnimationFrame(scan);
        };
        scan();
      }
    } catch (exception) { setError(exception.message || "Camera access was denied."); }
  };
  return <FeatureEmpty icon={<QrCode size={21} />} title="Scan a product QR code">
    <div className="qr-controls">
      {videoActive && <><video ref={videoRef} className="qr-video" muted playsInline /><button className="secondary-button" onClick={stopCamera}>Stop camera</button></>}
      {!videoActive && <button className="primary-button" onClick={startCamera}><QrCode size={16} /> Open camera</button>}
      <div className="search-field qr-search"><QrCode size={16} /><input value={productId} onChange={(event)=>setProductId(event.target.value)} onKeyDown={(event)=>event.key==="Enter"&&lookup(productId)} placeholder="Or enter product ID..." /></div>
      <button className="secondary-button" onClick={() => lookup(productId)}>Look up</button>
    </div>{error && <div className="inline-error">{error}</div>}
  </FeatureEmpty>;
}

function ClaimsView({ claims, products, withToken, withTokenBlob, onChanged }) {
  const [draft, setDraft] = useState(null);
  const [error, setError] = useState("");
  const save = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await withToken(draft.claimId ? `/api/claims/${draft.claimId}` : "/api/claims", {
        method: draft.claimId ? "PUT" : "POST",
        body: JSON.stringify(draft),
      });
      setDraft(null);
      await onChanged();
    } catch (exception) { setError(exception.message); }
  };
  const letter = async (claim) => {
    setError("");
    try {
      const blob = await withTokenBlob(`/api/claims/${claim.claimId}/letter`);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
      window.setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (exception) { setError(exception.message); }
  };
  return <section className="feature-page">
    <div className="feature-card">
      <div className="section-heading"><div><h2>Warranty claims</h2><p>Prepare claims and track their status</p></div><button className="primary-button" onClick={() => setDraft({ productId: products[0]?.productId || "", problemDescription: "", claimStatus: "Draft", serviceCenter: "", resolutionNotes: "" })}><Plus size={16} /> New claim</button></div>
      {draft && <form className="claim-form" onSubmit={save}>
        <div className="form-grid"><label>Product<select value={draft.productId} onChange={(event)=>setDraft({...draft, productId:event.target.value})}>{products.map((product)=><option key={product.productId} value={product.productId}>{product.productName}</option>)}</select></label><label>Status<select value={draft.claimStatus} onChange={(event)=>setDraft({...draft, claimStatus:event.target.value})}>{["Draft","Submitted","Under Review","Approved","Rejected","Resolved"].map((item)=><option key={item}>{item}</option>)}</select></label><label className="span-two">Problem description<textarea rows="3" value={draft.problemDescription} onChange={(event)=>setDraft({...draft, problemDescription:event.target.value})} required /></label><label>Service centre<input value={draft.serviceCenter} onChange={(event)=>setDraft({...draft, serviceCenter:event.target.value})} /></label><label>Resolution notes<input value={draft.resolutionNotes} onChange={(event)=>setDraft({...draft, resolutionNotes:event.target.value})} /></label></div>
        <div className="scanner-actions"><button type="button" className="secondary-button" onClick={()=>setDraft(null)}>Cancel</button><button className="primary-button">Save claim</button></div>
      </form>}
      {error && <div className="inline-error">{error}</div>}
      {claims.length ? <div className="claim-list">{claims.map((claim)=><div className="claim-row" key={claim.claimId}><div><strong>{products.find((item)=>item.productId===claim.productId)?.productName || "Product"}</strong><span>{claim.problemDescription}</span></div><span className="category-pill">{claim.claimStatus}</span><button className="secondary-button" onClick={()=>letter(claim)}><FileText size={15} /> Claim PDF</button><button className="icon-button" title="Edit claim" onClick={()=>setDraft(claim)}><Settings size={15} /></button></div>)}</div> : <div className="empty-state"><div className="empty-illustration"><ClipboardCheck size={24} /></div><h3>No warranty claims yet</h3><p>Create a claim to prepare documents and track its status.</p></div>}
    </div>
  </section>;
}

function MaintenanceView({ records, products, withToken, onChanged }) {
  const [draft, setDraft] = useState(null);
  const [error, setError] = useState("");
  const saveRecord = async (event) => {
    event.preventDefault();
    setError("");
    try {
      await withToken(draft.maintenanceId ? `/api/maintenance/${draft.maintenanceId}` : "/api/maintenance", { method: draft.maintenanceId ? "PUT" : "POST", body: JSON.stringify({ ...draft, cost: Number(draft.cost) }) });
      setDraft(null);
      await onChanged();
    } catch (exception) { setError(exception.message); }
  };
  const complete = async (record) => {
    try { await withToken(`/api/maintenance/${record.maintenanceId}/complete`, { method: "PATCH" }); await onChanged(); }
    catch (exception) { setError(exception.message); }
  };
  const today = new Date().toISOString().slice(0, 10);
  return <section className="feature-page"><div className="feature-card">
    <div className="section-heading"><div><h2>Maintenance</h2><p>Upcoming, overdue and completed work</p></div><button className="primary-button" onClick={()=>setDraft({ productId: products[0]?.productId || "", maintenanceTitle: "", description: "", scheduledDate: today, frequency: "Custom", status: "Scheduled", completionDate: null, cost: 0 })}><Plus size={16} /> Schedule maintenance</button></div>
    {draft && <form className="claim-form" onSubmit={saveRecord}><div className="form-grid"><label>Product<select value={draft.productId} onChange={(event)=>setDraft({...draft,productId:event.target.value})}>{products.map((product)=><option key={product.productId} value={product.productId}>{product.productName}</option>)}</select></label><label>Maintenance title<input value={draft.maintenanceTitle} onChange={(event)=>setDraft({...draft,maintenanceTitle:event.target.value})} required /></label><label className="span-two">Description<textarea rows="2" value={draft.description} onChange={(event)=>setDraft({...draft,description:event.target.value})} /></label><label>Scheduled date<input type="date" value={draft.scheduledDate} onChange={(event)=>setDraft({...draft,scheduledDate:event.target.value})} required /></label><label>Frequency<select value={draft.frequency} onChange={(event)=>setDraft({...draft,frequency:event.target.value})}><option>Custom</option><option>6 months</option><option>12 months</option></select></label><label>Cost<input type="number" min="0" step="0.01" value={draft.cost} onChange={(event)=>setDraft({...draft,cost:event.target.value})} /></label></div><div className="scanner-actions"><button type="button" className="secondary-button" onClick={()=>setDraft(null)}>Cancel</button><button className="primary-button">Save schedule</button></div></form>}
    {error && <div className="inline-error">{error}</div>}
    {records.length ? <div className="claim-list">{records.map((record)=><div className="claim-row" key={record.maintenanceId}><div><strong>{record.maintenanceTitle}</strong><span>{products.find((item)=>item.productId===record.productId)?.productName || "Product"} · {shortDate(record.scheduledDate)}</span></div><span className="category-pill">{record.status}</span>{record.status !== "Completed" && <button className="secondary-button" onClick={()=>complete(record)}><Check size={15} /> Complete</button>}<button className="icon-button" title="Edit maintenance" onClick={()=>setDraft(record)}><Settings size={15} /></button></div>)}</div> : <div className="empty-state"><div className="empty-illustration"><CalendarDays size={24} /></div><h3>No maintenance schedules yet</h3><p>Add routine care for a product to receive reminder notifications.</p></div>}
  </div></section>;
}

function AnalyticsView({ analytics }) {
  if (!analytics) return <div className="table-loading"><span className="spinner" />Loading analytics…</div>;
  const maxPurchase = Math.max(1, ...(analytics.monthlyPurchaseSpending || []).map((item)=>item.spend));
  return <section className="feature-page"><div className="analytics-grid">
    <div className="feature-card metric-card"><span>Total purchase spending</span><strong className="metric-value">{money(analytics.totalPurchaseSpending)}</strong></div>
    <div className="feature-card metric-card"><span>Maintenance spending</span><strong className="metric-value">{money(analytics.totalMaintenanceSpending)}</strong></div>
    <div className="feature-card"><h3>Warranty status</h3>{analytics.warrantyStatusDistribution.map((item)=><div className="category-row" key={item.status}><div className="category-label"><span>{item.status}</span><span>{item.count}</span></div><div className="bar-track"><span className="category-bar" style={{width:`${Math.max(7,item.count/Math.max(1,analytics.totalProducts)*100)}%`}} /></div></div>)}</div>
    <div className="feature-card"><h3>Monthly purchases</h3><div className="bar-chart">{analytics.monthlyPurchaseSpending.map((item)=><div className="chart-column" key={item.month}><span title={`${item.month}: ${money(item.spend)}`} style={{height:`${Math.max(8,item.spend/maxPurchase*100)}%`}} /><small>{item.month.slice(5)}</small></div>)}</div></div>
    <div className="feature-card"><h3>Upcoming expirations</h3>{Object.entries(analytics.expiryWindows).map(([days,count])=><div className="category-row" key={days}><div className="category-label"><span>Next {days} days</span><span>{count}</span></div></div>)}</div>
    <div className="feature-card"><h3>Maintenance status</h3>{Object.entries(analytics.maintenanceStatus).map(([status,count])=><div className="category-row" key={status}><div className="category-label"><span>{status}</span><span>{count}</span></div></div>)}</div>
  </div></section>;
}

function ProductGlyph({ product }) {
  const tone = ["blue", "purple", "green", "amber"][Math.abs((product.productName || "").length) % 4];
  return <span className={`product-glyph glyph-${tone}`}><Package size={17} /></span>;
}

function ServiceHistory({ records, loading, search, onSearch }) {
  return <>
    <div className="section-heading">
      <div><h2>Service history</h2><p>{records.length} {records.length === 1 ? "record" : "records"} across your products</p></div>
      <div className="search-field"><Search size={16} /><input value={search} onChange={(event) => onSearch(event.target.value)} placeholder="Search service records..." /></div>
    </div>
    {loading ? <div className="table-loading"><span className="spinner" />Loading service history…</div> : records.length ? <div className="table-wrap"><table className="product-table"><thead><tr><th>PRODUCT</th><th>SERVICE DATE</th><th>PROVIDER</th><th>DESCRIPTION</th><th>COST</th></tr></thead><tbody>
      {records.map((record) => <tr key={record.serviceId}><td><div className="product-cell"><ProductGlyph product={{ productName: record.productName }} /><span><strong>{record.productName}</strong></span></div></td><td>{shortDate(record.serviceDate)}</td><td>{record.provider}</td><td>{record.description}</td><td>{money(record.cost)}</td></tr>)}
    </tbody></table></div> : <div className="empty-state"><div className="empty-illustration"><Activity size={25} /></div><h3>No service records yet</h3><p>Open any product and add a service record to build its maintenance timeline.</p></div>}
  </>;
}

function ProductTable({ products, loading, onSelect, onEdit, onDelete }) {
  if (loading) return <div className="table-loading"><span className="spinner" />Loading products…</div>;
  if (!products.length) return <div className="empty-state"><div className="empty-illustration"><Package size={26} /></div><h3>Nothing here just yet</h3><p>Products you add will appear here, ready to keep their details and warranty dates close.</p></div>;
  return <div className="table-wrap"><table className="product-table"><thead><tr><th>PRODUCT</th><th>CATEGORY</th><th>PURCHASE DATE</th><th>WARRANTY ENDS</th><th>STATUS</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>
    {products.map((product) => <tr key={product.productId} onClick={() => onSelect(product)} className="product-row">
      <td><div className="product-cell"><ProductGlyph product={product} /><span><strong>{product.productName}</strong><small>{product.brand || product.modelNumber || "—"}</small></span></div></td>
      <td><span className="category-pill">{product.category || "Other"}</span></td><td>{shortDate(product.purchaseDate)}</td>
      <td><span className="expiry-date">{shortDate(product.expiryDate)}</span></td>
      <td><StatusBadge product={product} /></td>
      <td><div className="row-actions" onClick={(event) => event.stopPropagation()}><button className="icon-button" title="Edit product" onClick={() => onEdit(product)}><Settings size={15} /></button><button className="icon-button" title="Delete product" onClick={() => onDelete(product)}><X size={16} /></button></div></td>
    </tr>)}
  </tbody></table></div>;
}

function StatusBadge({ product }) {
  if (product.warrantyStatus === "expired") return <span className="status-badge status-expired"><span />Expired</span>;
  if (product.warrantyDaysRemaining <= 30) return <span className="status-badge status-expiring"><span />{product.warrantyDaysRemaining === 0 ? "Expires today" : `${product.warrantyDaysRemaining} days left`}</span>;
  return <span className="status-badge status-active"><span />Active</span>;
}

function ProductModal({ product, file, onClose, onSave, onFile }) {
  const [values, setValues] = useState(product ? { ...blankProduct, ...product } : { ...blankProduct });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const change = (event) => setValues((current) => ({ ...current, [event.target.name]: event.target.value }));
  return <Modal onClose={onClose} wide>
    <form className="product-form" onSubmit={async (event) => {
      event.preventDefault();
      setBusy(true);
      setError("");
      try { await onSave({ ...values, warrantyDuration: Number(values.warrantyDuration), purchasePrice: Number(values.purchasePrice) }, product); }
      catch (exception) { setError(exception.message); }
      finally { setBusy(false); }
    }}>
      <div className="modal-header"><div><div className="eyebrow muted-eyebrow">{product ? "UPDATE YOUR RECORD" : "GROW YOUR COLLECTION"}</div><h2>{product ? "Edit product" : "Add a product"}</h2><p>Keep all the important details together.</p></div><button type="button" className="icon-button modal-close" onClick={onClose} aria-label="Close"><X size={19} /></button></div>
      <div className="form-section-label"><span>PRODUCT DETAILS</span><i /></div>
      <div className="form-grid">
        <label className="span-two">Product name *<input name="productName" value={values.productName} onChange={change} placeholder="e.g. MacBook Air" required maxLength="120" /></label>
        <label>Brand<input name="brand" value={values.brand} onChange={change} placeholder="e.g. Apple" /></label>
        <label>Category<select name="category" value={values.category} onChange={change}>{["Electronics", "Appliances", "Furniture", "Tools", "Fitness", "Other"].map((item) => <option key={item}>{item}</option>)}</select></label>
        <label>Model number<input name="modelNumber" value={values.modelNumber} onChange={change} placeholder="Optional" /></label>
        <label>Serial number<input name="serialNumber" value={values.serialNumber} onChange={change} placeholder="Optional" /></label>
      </div>
      <div className="form-section-label"><span>PURCHASE & WARRANTY</span><i /></div>
      <div className="form-grid">
        <label>Purchase date *<input name="purchaseDate" type="date" value={String(values.purchaseDate).slice(0, 10)} onChange={change} required /></label>
        <label>Warranty duration <span className="label-suffix">in months</span><input name="warrantyDuration" type="number" min="0" max="600" value={values.warrantyDuration} onChange={change} required /></label>
        <label>Purchase price<input name="purchasePrice" type="number" min="0" step="0.01" value={values.purchasePrice} onChange={change} /></label>
        <label>Seller<input name="seller" value={values.seller} onChange={change} placeholder="Store or retailer" /></label>
      </div>
      <div className="form-section-label"><span>DOCUMENTS & NOTES</span><i /></div>
      <div className="form-grid">
        <label className="span-two upload-label">Invoice <span className="label-suffix">PDF, JPG, PNG or WebP · max 10 MB</span><span className="upload-box"><UploadCloud size={19} /><span>{file?.name || (product?.invoiceStoragePath ? "Replace existing invoice" : "Choose an invoice to upload")}</span><input type="file" accept=".pdf,image/jpeg,image/png,image/webp" onChange={(event) => onFile(event.target.files?.[0] || null)} /></span></label>
        <label className="span-two">Notes<textarea name="notes" value={values.notes} onChange={change} rows="2" placeholder="Anything else worth remembering?" maxLength="2000" /></label>
      </div>
      {error && <div className="inline-error">{error}</div>}
      <div className="modal-footer"><span className="required-note">* Required fields</span><div><button type="button" className="secondary-button" onClick={onClose}>Cancel</button><button disabled={busy} className="primary-button">{busy ? "Saving…" : product ? "Save changes" : "Add product"}</button></div></div>
    </form>
  </Modal>;
}

function DetailsModal({ product, token, onClose, onChanged, onToast }) {
  const [services, setServices] = useState([]);
  const [serviceForm, setServiceForm] = useState(false);
  const [serviceBusy, setServiceBusy] = useState(false);
  const [error, setError] = useState("");
  const loadServices = async () => {
    try {
      const data = await api(`/api/products/${product.productId}/services`, await token());
      setServices(data.items);
    } catch (exception) { setError(exception.message); }
  };
  useEffect(() => { loadServices(); }, [product.productId]);
  const invoice = async () => {
    const invoiceWindow = window.open("about:blank", "_blank");
    if (invoiceWindow) invoiceWindow.opener = null;
    try {
      const file = await apiBlob(`/api/invoices/${product.productId}/download`, await token());
      const fileUrl = URL.createObjectURL(file);
      if (invoiceWindow) invoiceWindow.location.replace(fileUrl);
      else window.location.assign(fileUrl);
      window.setTimeout(() => URL.revokeObjectURL(fileUrl), 60000);
    } catch (exception) {
      invoiceWindow?.close();
      setError(exception.message);
    }
  };
  return <Modal onClose={onClose} wide>
    <div className="details-modal">
      <div className="modal-header"><div><div className="eyebrow muted-eyebrow">PRODUCT DETAILS</div><h2>{product.productName}</h2><p>{[product.brand, product.modelNumber].filter(Boolean).join(" · ") || product.category}</p></div><button className="icon-button modal-close" onClick={onClose} aria-label="Close"><X size={19} /></button></div>
      <div className="detail-summary"><ProductGlyph product={product} /><div><StatusBadge product={product} /><span>Warranty ends {shortDate(product.expiryDate)}</span></div><strong>{product.warrantyDaysRemaining < 0 ? `${Math.abs(product.warrantyDaysRemaining)} days ago` : product.warrantyDaysRemaining === 0 ? "Today" : `${product.warrantyDaysRemaining} days left`}</strong></div>
      <div className="details-grid">
        <Detail label="Category" value={product.category} /><Detail label="Purchase date" value={shortDate(product.purchaseDate)} />
        <Detail label="Purchase price" value={money(product.purchasePrice)} /><Detail label="Warranty duration" value={`${product.warrantyDuration} months`} />
        <Detail label="Seller" value={product.seller} /><Detail label="Serial number" value={product.serialNumber} />
      </div>
      {product.notes && <div className="notes-block"><span>NOTES</span><p>{product.notes}</p></div>}
      <div className="detail-actions">{product.invoiceStoragePath ? <button className="secondary-button" onClick={invoice}><FileText size={16} /> View invoice</button> : <span className="no-invoice"><FileText size={15} /> No invoice attached</span>}<button className="secondary-button" onClick={() => setServiceForm(serviceForm === true ? false : true)}><Plus size={16} /> Add service record</button></div>
      {serviceForm === true && <ServiceForm productId={product.productId} token={token} onDone={async () => { setServiceForm(false); await loadServices(); await onChanged(); onToast("Service record saved."); }} onCancel={() => setServiceForm(false)} onError={setError} onBusy={setServiceBusy} busy={serviceBusy} />}
      <div className="service-list-heading"><div><h3>Service history</h3><span>{services.length} {services.length === 1 ? "record" : "records"}</span></div></div>
      {services.length ? <div className="service-list">{services.map((record) => <div className="service-record-wrap" key={record.serviceId}>
        <div className="service-entry"><span className="service-entry-icon"><Activity size={16} /></span><div><strong>{record.description}</strong><span>{record.provider} · {shortDate(record.serviceDate)}</span></div><b>{money(record.cost)}</b><div className="service-entry-actions"><button className="icon-button" title="Edit service record" onClick={() => setServiceForm(record)}><Settings size={14} /></button><button className="icon-button" title="Delete service record" onClick={async () => {
          if (!window.confirm("Delete this service record?")) return;
          setServiceBusy(true);
          try {
            await api(`/api/products/${product.productId}/services/${record.serviceId}`, await token(), { method: "DELETE" });
            await loadServices();
            await onChanged();
            onToast("Service record deleted.");
          } catch (exception) { setError(exception.message); }
          finally { setServiceBusy(false); }
        }}><X size={14} /></button></div></div>
        {serviceForm?.serviceId === record.serviceId && <ServiceForm productId={product.productId} initial={record} token={token} onDone={async () => { setServiceForm(false); await loadServices(); await onChanged(); onToast("Service record updated."); }} onCancel={() => setServiceForm(false)} onError={setError} onBusy={setServiceBusy} busy={serviceBusy} />}
      </div>)}</div> : <div className="service-empty">No service visits yet. Add one to start a maintenance timeline.</div>}
      {error && <div className="inline-error">{error}</div>}
      <div className="modal-footer"><span className="required-note">{product.seller ? `Purchased from ${product.seller}` : "Product record"}</span><button className="secondary-button" onClick={onClose}>Done</button></div>
    </div>
  </Modal>;
}

function Detail({ label, value }) {
  return <div className="detail-item"><span>{label}</span><strong>{value || "—"}</strong></div>;
}

function ServiceForm({ productId, initial, token, onDone, onCancel, onError, onBusy, busy }) {
  const [form, setForm] = useState(initial ? { ...initial } : { serviceDate: new Date().toISOString().slice(0, 10), provider: "", description: "", cost: 0, notes: "" });
  const set = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  return <form className="service-form" onSubmit={async (event) => {
    event.preventDefault();
    onBusy(true);
    try {
      await api(`/api/products/${productId}/services${initial ? `/${initial.serviceId}` : ""}`, await token(), { method: initial ? "PUT" : "POST", body: JSON.stringify({ ...form, cost: Number(form.cost) }) });
      await onDone();
    } catch (error) { onError(error.message); }
    finally { onBusy(false); }
  }}>
    <div className="service-form-grid"><label>Date<input type="date" name="serviceDate" value={form.serviceDate} onChange={set} required /></label><label>Service provider<input name="provider" value={form.provider} onChange={set} required placeholder="e.g. Authorized repair center" /></label><label className="span-two">What was done?<input name="description" value={form.description} onChange={set} required placeholder="Describe the service or repair" /></label><label>Cost<input type="number" name="cost" min="0" step="0.01" value={form.cost} onChange={set} /></label></div>
    <div className="service-form-actions"><button className="secondary-button" type="button" onClick={onCancel}>Cancel</button><button className="primary-button" disabled={busy}>{busy ? "Saving…" : initial ? "Update record" : "Save record"}</button></div>
  </form>;
}

function NotificationsModal({ items, onClose, onRead }) {
  return <Modal onClose={onClose}>
    <div className="notifications-modal"><div className="modal-header"><div><div className="eyebrow muted-eyebrow">STAY IN THE LOOP</div><h2>Notifications</h2><p>Important warranty dates, all in one place.</p></div><button className="icon-button modal-close" onClick={onClose} aria-label="Close"><X size={19} /></button></div>
      {items.length ? <div className="notification-list">{items.map((item) => <div className={`notification-item ${item.read ? "notification-read" : ""}`} key={item.notificationId}><span className="notification-icon"><Clock3 size={16} /></span><div><strong>{item.productName} warranty {item.daysBeforeExpiry === 0 ? "expires today" : `expires in ${item.daysBeforeExpiry} days`}</strong><span>Warranty ends {shortDate(item.expiryDate)}</span></div>{!item.read && <button className="mark-read" onClick={() => onRead(item)} aria-label="Mark as read"><Check size={16} /></button>}</div>)}</div> : <div className="notification-empty"><Bell size={22} /><strong>You're all caught up</strong><span>Expiry reminders will show up here.</span></div>}
      <div className="modal-footer"><span className="required-note">Automatic reminders at 30, 7, and 0 days</span><button className="secondary-button" onClick={onClose}>Close</button></div>
    </div>
  </Modal>;
}

function Modal({ children, onClose, wide = false }) {
  useEffect(() => {
    const closeOnEscape = (event) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", closeOnEscape);
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", closeOnEscape); document.body.style.overflow = ""; };
  }, [onClose]);
  return <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><div className={`modal-card ${wide ? "modal-wide" : ""}`} role="dialog" aria-modal="true">{children}</div></div>;
}

export default App;
