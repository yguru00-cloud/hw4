import Bulldog from './Bulldog'

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-inner">
        <Bulldog className="footer-dog" />
        <div className="footer-text">
          <p className="footer-motto">Lux et Veritas</p>
          <p className="footer-sub">Light and Truth · Est. 1701</p>
          <p className="footer-note">
            Campus Customs · Boola Boola! · Go Bulldogs! Say hi to Handsome Dan.
          </p>
        </div>
      </div>
    </footer>
  )
}
