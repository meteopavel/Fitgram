import styles from './style.module.css'
import { Container, LinkComponent } from '../index'

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return <footer className={styles.footer}>
      <Container className={styles.footer__container}>
        <LinkComponent 
          href='#'
          title={`Fitgram © ${currentYear}`}
          className={styles.footer__brand} />
      </Container>
  </footer>
}

export default Footer
