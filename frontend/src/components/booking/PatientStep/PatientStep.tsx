import { forwardRef, useEffect, useImperativeHandle } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import type { BookingStepProps } from '../types';
import styles from './PatientStep.module.css';

const patientSchema = z.object({
  patientName: z.string().trim().min(2, 'Vui lòng nhập họ tên'),
  patientPhone: z
    .string()
    .trim()
    .regex(/^(0|\+84)\d{9}$/, 'Số điện thoại không hợp lệ'),
  patientEmail: z.union([z.literal(''), z.email('Email không hợp lệ')]),
  patientDob: z.string().min(1, 'Vui lòng chọn ngày sinh'),
  patientGender: z.enum(['male', 'female', 'other'], {
    message: 'Vui lòng chọn giới tính',
  }),
  symptoms: z.string().max(500, 'Nội dung tối đa 500 ký tự'),
});

type PatientFormValues = z.infer<typeof patientSchema>;

export interface PatientStepHandle {
  validate: () => Promise<boolean>;
}

export const PatientStep = forwardRef<PatientStepHandle, BookingStepProps>(
  function PatientStep({ data, update }, ref) {
    const {
      register,
      handleSubmit,
      watch,
      formState: { errors },
    } = useForm<PatientFormValues>({
      resolver: zodResolver(patientSchema),
      mode: 'onSubmit',
      reValidateMode: 'onChange',
      defaultValues: {
        patientName: data.patientName,
        patientPhone: data.patientPhone,
        patientEmail: data.patientEmail,
        patientDob: data.patientDob,
        patientGender: data.patientGender || undefined,
        symptoms: data.symptoms,
      },
    });

    useEffect(() => {
      const subscription = watch((values) => {
        update({
          patientName: values.patientName ?? '',
          patientPhone: values.patientPhone ?? '',
          patientEmail: values.patientEmail ?? '',
          patientDob: values.patientDob ?? '',
          patientGender: values.patientGender ?? '',
          symptoms: values.symptoms ?? '',
        });
      });

      return () => {
        subscription.unsubscribe();
      };
    }, [update, watch]);

    useImperativeHandle(ref, () => ({
      validate: () =>
        new Promise<boolean>((resolve) => {
          void handleSubmit(
            (values) => {
              update(values);
              resolve(true);
            },
            () => resolve(false),
          )();
        }),
    }));

    return (
      <form className={styles.form} onSubmit={(event) => event.preventDefault()}>
        <label>
          Họ và tên người khám *
          <input {...register('patientName')} placeholder="Nguyễn Văn A" />
          {errors.patientName && <small>{errors.patientName.message}</small>}
        </label>

        <div>
          <label>
            Số điện thoại *
            <input
              {...register('patientPhone')}
              inputMode="tel"
              placeholder="0912 345 678"
            />
            {errors.patientPhone && <small>{errors.patientPhone.message}</small>}
          </label>
          <label>
            Email
            <input
              {...register('patientEmail')}
              type="email"
              placeholder="email@example.com"
            />
            {errors.patientEmail && <small>{errors.patientEmail.message}</small>}
          </label>
        </div>

        <div>
          <label>
            Ngày sinh *
            <input {...register('patientDob')} type="date" />
            {errors.patientDob && <small>{errors.patientDob.message}</small>}
          </label>
          <fieldset>
            <legend>Giới tính *</legend>
            <label>
              <input {...register('patientGender')} type="radio" value="male" />
              Nam
            </label>
            <label>
              <input {...register('patientGender')} type="radio" value="female" />
              Nữ
            </label>
            <label>
              <input {...register('patientGender')} type="radio" value="other" />
              Khác
            </label>
            {errors.patientGender && <small>{errors.patientGender.message}</small>}
          </fieldset>
        </div>

        <label>
          Triệu chứng hoặc yêu cầu
          <textarea
            {...register('symptoms')}
            rows={4}
            placeholder="Mô tả ngắn triệu chứng, tiền sử hoặc yêu cầu hỗ trợ..."
          />
          {errors.symptoms && <small>{errors.symptoms.message}</small>}
        </label>

        <p>
          Thông tin được bảo mật và chỉ dùng cho mục đích tiếp nhận, chăm sóc
          người bệnh.
        </p>
      </form>
    );
  },
);
