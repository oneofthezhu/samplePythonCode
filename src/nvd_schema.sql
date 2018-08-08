--
-- PostgreSQL database dump
--

-- Dumped from database version 10.4
-- Dumped by pg_dump version 10.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: DATABASE postgres; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON DATABASE postgres IS 'default administrative connection database';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: adminpack; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS adminpack WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION adminpack; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION adminpack IS 'administrative functions for PostgreSQL';


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: vendorinfo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.vendorinfo (
    id integer NOT NULL,
    vendor_name character varying(100),
    product_name character varying(100)
);


ALTER TABLE public.vendorinfo OWNER TO postgres;

--
-- Name: VendorInfo_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."VendorInfo_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."VendorInfo_id_seq" OWNER TO postgres;

--
-- Name: VendorInfo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."VendorInfo_id_seq" OWNED BY public.vendorinfo.id;


--
-- Name: affectedvendors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.affectedvendors (
    cve_id character varying(16),
    vendor_id integer,
    version_value character varying(120)
);


ALTER TABLE public.affectedvendors OWNER TO postgres;

--
-- Name: basemetricv2; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.basemetricv2 (
    cve_id character varying(16) NOT NULL,
    access_vector text,
    base_score double precision NOT NULL,
    exploitability_score double precision NOT NULL,
    impact_score double precision NOT NULL,
    vector_string character varying(75),
    severity_value character varying(10)
);


ALTER TABLE public.basemetricv2 OWNER TO postgres;

--
-- Name: basemetricv3; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.basemetricv3 (
    vector_string character varying(75),
    attack_vector character varying(25),
    base_score double precision,
    base_severity character varying(10),
    exploitability_score double precision,
    impact_score double precision,
    cve_id character varying(16) NOT NULL
);


ALTER TABLE public.basemetricv3 OWNER TO postgres;

--
-- Name: cpe; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cpe (
    cve_id character varying(16) NOT NULL,
    cpe22uri character varying(150) NOT NULL,
    cpe23uri character varying(150) NOT NULL,
    version_start_excluding character varying(50),
    version_start_including character varying(50),
    version_end_excluding character varying(50),
    version_end_including character varying(50)
);


ALTER TABLE public.cpe OWNER TO postgres;

--
-- Name: cve; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cve (
    id character varying(16) NOT NULL,
    description text,
    publisheddate timestamp without time zone NOT NULL,
    lastmodifieddate timestamp without time zone NOT NULL
);


ALTER TABLE public.cve OWNER TO postgres;

--
-- Name: vendorinfo id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendorinfo ALTER COLUMN id SET DEFAULT nextval('public."VendorInfo_id_seq"'::regclass);


--
-- Name: cve CVE_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cve
    ADD CONSTRAINT "CVE_pkey" PRIMARY KEY (id);


--
-- Name: vendorinfo VendorInfo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendorinfo
    ADD CONSTRAINT "VendorInfo_pkey" PRIMARY KEY (id);


--
-- Name: basemetricv2 basemetricv2_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.basemetricv2
    ADD CONSTRAINT basemetricv2_pkey PRIMARY KEY (cve_id);


--
-- Name: basemetricv3 basemetricv3_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.basemetricv3
    ADD CONSTRAINT basemetricv3_pkey PRIMARY KEY (cve_id);


--
-- Name: vendorinfo vendorName_ProdName_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.vendorinfo
    ADD CONSTRAINT "vendorName_ProdName_uniq" UNIQUE (vendor_name, product_name);


--
-- Name: basemetricv2 cve_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.basemetricv2
    ADD CONSTRAINT cve_id FOREIGN KEY (cve_id) REFERENCES public.cve(id) ON DELETE CASCADE;


--
-- Name: basemetricv3 cve_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.basemetricv3
    ADD CONSTRAINT cve_id FOREIGN KEY (cve_id) REFERENCES public.cve(id) ON DELETE CASCADE;


--
-- Name: cpe cve_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cpe
    ADD CONSTRAINT cve_id FOREIGN KEY (cve_id) REFERENCES public.cve(id) ON DELETE CASCADE;


--
-- Name: affectedvendors cve_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.affectedvendors
    ADD CONSTRAINT cve_id FOREIGN KEY (cve_id) REFERENCES public.cve(id) ON DELETE CASCADE;


--
-- Name: affectedvendors vendor_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.affectedvendors
    ADD CONSTRAINT vendor_id FOREIGN KEY (vendor_id) REFERENCES public.vendorinfo(id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

