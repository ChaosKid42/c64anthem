;=====================================================================
;  "DAS LIED DER DEUTSCHEN" - 3. STROPHE
;  C64-Programm, ACME-Syntax
;
;  Bild  : Multicolor-Bitmap 320x200, Darstellung des Bundes-
;          praesidenten + Text der dritten Strophe
;  Musik : SID-Arrangement der Haydn-Melodie, 3 Stimmen, 50-Hz-IRQ
;
;  Bauen :  acme -o hymne.prg hymne.asm
;  Dateien im gleichen Verzeichnis: screen.bin, colors.bin,
;           bitmap.bin, freq.bin  (erzeugt von make_data.py)
;  Start :  LOAD"HYMNE",8,1   bzw.  RUN
;=====================================================================

!to "hymne.prg", cbm

;--- BASIC-Zeile  10 SYS 2061 ---------------------------------------
* = $0801
        !word $080b
        !word 10
        !byte $9e
        !text "2061"
        !byte 0
        !word 0

;--- Zeropage -------------------------------------------------------
mptr    = $fb           ; Zeiger in die Musikdaten
durcnt  = $fd           ; Restdauer der Note in 1/50 s
pwmcnt  = $fe           ; Zaehler Pulsbreitenmodulation
prev1   = $f7           ; zuletzt gespielte Note St. 1..3
prev2   = $f8
prev3   = $f9

;=====================================================================
* = $080d
start
        sei
        lda #$7f
        sta $dc0d       ; CIA-Timer-IRQs aus
        lda $dc0d

        lda #$03
        sta $dd00       ; VIC-Bank 0 ($0000-$3fff)
        lda #$18
        sta $d018       ; Bitmap $2000, Screen $0400
        lda #$3b
        sta $d011       ; Bitmap-Modus, 25 Zeilen
        lda #$d8
        sta $d016       ; Multicolor, 40 Spalten
        lda #$00
        sta $d020       ; Rahmen schwarz
        sta $d021       ; Hintergrund schwarz

;--- Bilddaten kopieren ---------------------------------------------
        ldx #$00
copy    lda screen,x
        sta $0400,x
        lda screen+$100,x
        sta $0500,x
        lda screen+$200,x
        sta $0600,x
        lda screen+$300,x
        sta $0700,x
        lda colors,x
        sta $d800,x
        lda colors+$100,x
        sta $d900,x
        lda colors+$200,x
        sta $da00,x
        lda colors+$300,x
        sta $db00,x
        inx
        bne copy

;--- SID ------------------------------------------------------------
        ldx #$18
        lda #$00
sidclr  sta $d400,x
        dex
        bpl sidclr
        lda #$0f
        sta $d418       ; Lautstaerke 15, Filter aus

        lda #$00        ; Stimme 1: Melodie, Pulswelle
        sta $d402
        lda #$0c
        sta $d403       ; Pulsbreite $0c00
        lda #$09
        sta $d405       ; Attack 0, Decay 9
        lda #$a8
        sta $d406       ; Sustain 10, Release 8

        lda #$00        ; Stimme 2: Bass, Dreieck
        sta $d409
        lda #$0c
        sta $d40a
        lda #$00
        sta $d40c
        lda #$a9
        sta $d40d

        lda #$00        ; Stimme 3: Flaeche, Saegezahn
        sta $d410
        lda #$08
        sta $d411
        lda #$09
        sta $d413
        lda #$66
        sta $d414

;--- Raster-IRQ -----------------------------------------------------
        lda #$fb
        sta $d012       ; Rasterzeile 251
        lda $d011
        and #$7f
        sta $d011
        lda #$01
        sta $d01a
        lda #<irq
        sta $0314
        lda #>irq
        sta $0315
        lda #1
        sta durcnt
        lda #0          ; noch keine Note gespielt -> erste Note klingt
        sta prev1
        sta prev2
        sta prev3
        lda #<music
        sta mptr
        lda #>music
        sta mptr+1
        cli

main    jmp main        ; alles Weitere macht der IRQ

;--- IRQ ------------------------------------------------------------
irq     pha
        txa
        pha
        tya
        pha
        lda #$01
        sta $d019       ; IRQ quittieren
        jsr tick
        pla
        tay
        pla
        tax
        pla
        jmp $ea31       ; KERNAL-IRQ-Ende

;--- Takt: alle 20 ms ein Schritt, Pulsbreite langsam wandern --------
tick    dec durcnt
        bne tick1
        jsr nextev
tick1   inc pwmcnt
        lda pwmcnt
        and #$03
        bne tick2
        inc $d403
        lda $d403
        cmp #$10
        bcc tick2
        lda #$08
        sta $d403
tick2   rts

;--- naechsten Block holen: Note1, Note2, Note3, Dauer ---------------
nextev  ldy #0
        lda (mptr),y
        cmp #$ff
        bne nextev1
        lda #<music     ; Ende -> von vorn
        sta mptr
        lda #>music
        sta mptr+1
nextev1 ldy #0
        lda (mptr),y
        jsr set1
        ldy #1
        lda (mptr),y
        jsr set2
        ldy #2
        lda (mptr),y
        jsr set3
        ldy #3
        lda (mptr),y
        sta durcnt
        lda mptr
        clc
        adc #4
        sta mptr
        bcc nextev2
        inc mptr+1
nextev2 rts

;--- Stimme 1 (A = MIDI-Note, 0 = Pause) ----------------------------
set1    cmp #$00
        bne set1a
        lda #$40
        sta $d404
        lda #$00
        sta prev1
        rts
set1a   cmp prev1
        beq set1b       ; gleiche Note -> Gate bleibt offen
        sta prev1
        sec
        sbc #36
        asl
        tay
        lda freqtbl,y
        sta $d400
        lda freqtbl+1,y
        sta $d401
        lda #$41        ; Pulswelle + Gate
        sta $d404
set1b   rts

;--- Stimme 2 (Bass) ------------------------------------------------
set2    cmp #$00
        bne set2a
        lda #$40
        sta $d40b
        lda #$00
        sta prev2
        rts
set2a   cmp prev2
        beq set2b
        sta prev2
        sec
        sbc #36
        asl
        tay
        lda freqtbl,y
        sta $d407
        lda freqtbl+1,y
        sta $d408
        lda #$11        ; Dreieck + Gate
        sta $d40b
set2b   rts

;--- Stimme 3 (Flaeche) ---------------------------------------------
set3    cmp #$00
        bne set3a
        lda #$40
        sta $d412
        lda #$00
        sta prev3
        rts
set3a   cmp prev3
        beq set3b
        sta prev3
        sec
        sbc #36
        asl
        tay
        lda freqtbl,y
        sta $d40e
        lda freqtbl+1,y
        sta $d40f
        lda #$21        ; Saegezahn + Gate
        sta $d412
set3b   rts

;--- Frequenztabelle MIDI 36..84, PAL: f * 16777216 / 985248 --------
freqtbl
        !bin "freq.bin"

;--- Musik: Note1, Note2, Note3, Dauer (1/50 s), $ff = Ende ---------
music
        !bin "music.bin"

;--- Bilddaten ------------------------------------------------------
* = $1000
screen
        !bin "screen.bin"

* = $1400
colors
        !bin "colors.bin"

* = $2000
bitmap
        !bin "bitmap.bin"