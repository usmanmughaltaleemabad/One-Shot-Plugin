"""
Spring Batch Code Generator - Job definitions, step configuration, readers/processors/writers
"""

from typing import Dict


def generate_spring_batch_job_config() -> Dict[str, str]:
    """Generate Spring Batch job configuration"""
    return {
        "BatchConfiguration.java": '''package com.example.batch.config;

import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.configuration.annotation.EnableBatchProcessing;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.item.ItemWriter;
import org.springframework.batch.item.database.JdbcCursorItemReader;
import org.springframework.batch.item.database.builder.JdbcCursorItemReaderBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.transaction.PlatformTransactionManager;
import javax.sql.DataSource;

@Configuration
@EnableBatchProcessing
public class BatchConfiguration {

    @Bean
    public JobLauncher jobLauncher(JobRepository jobRepository) throws Exception {
        return new org.springframework.batch.core.launch.support.SimpleJobLauncher() {{
            setJobRepository(jobRepository);
            afterPropertiesSet();
        }};
    }

    @Bean
    public Job processJob(
        JobRepository jobRepository,
        Step processingStep,
        JobCompletionNotificationListener listener
    ) {
        return new JobBuilder("processJob", jobRepository)
            .listener(listener)
            .start(processingStep)
            .build();
    }

    @Bean
    public Step processingStep(
        JobRepository jobRepository,
        PlatformTransactionManager transactionManager,
        ItemReader<InputData> reader,
        ItemProcessor<InputData, OutputData> processor,
        ItemWriter<OutputData> writer
    ) {
        return new StepBuilder("processingStep", jobRepository)
            .<InputData, OutputData>chunk(100, transactionManager)
            .reader(reader)
            .processor(processor)
            .writer(writer)
            .faultTolerant()
            .skipLimit(10)
            .skip(org.springframework.batch.item.file.FlatFileParseException.class)
            .retryLimit(3)
            .retry(org.springframework.dao.DeadlockLoserDataAccessException.class)
            .build();
    }

    @Bean
    public JdbcCursorItemReader<InputData> itemReader(DataSource dataSource) {
        return new JdbcCursorItemReaderBuilder<InputData>()
            .name("itemReader")
            .dataSource(dataSource)
            .sql("SELECT id, name, value FROM input_data WHERE processed = false")
            .rowMapper(new InputDataRowMapper())
            .build();
    }

    @Bean
    public ItemProcessor<InputData, OutputData> itemProcessor() {
        return new DataProcessingItemProcessor();
    }

    @Bean
    public ItemWriter<OutputData> itemWriter(JdbcTemplate jdbcTemplate) {
        return new DatabaseItemWriter(jdbcTemplate);
    }
}
''',
        "InputData.java": '''package com.example.batch.model;

public class InputData {
    private Long id;
    private String name;
    private Integer value;
    private Boolean processed;

    // Constructors, getters, setters
    public InputData() {}

    public InputData(Long id, String name, Integer value) {
        this.id = id;
        this.name = name;
        this.value = value;
        this.processed = false;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Integer getValue() { return value; }
    public void setValue(Integer value) { this.value = value; }

    public Boolean getProcessed() { return processed; }
    public void setProcessed(Boolean processed) { this.processed = processed; }

    @Override
    public String toString() {
        return "InputData{" +
            "id=" + id +
            ", name='" + name + '\\'' +
            ", value=" + value +
            ", processed=" + processed +
            '}';
    }
}
''',
        "OutputData.java": '''package com.example.batch.model;

public class OutputData {
    private Long id;
    private String name;
    private Integer processedValue;
    private Long processedTimestamp;

    public OutputData() {}

    public OutputData(Long id, String name, Integer processedValue) {
        this.id = id;
        this.name = name;
        this.processedValue = processedValue;
        this.processedTimestamp = System.currentTimeMillis();
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Integer getProcessedValue() { return processedValue; }
    public void setProcessedValue(Integer processedValue) { this.processedValue = processedValue; }

    public Long getProcessedTimestamp() { return processedTimestamp; }
    public void setProcessedTimestamp(Long processedTimestamp) { this.processedTimestamp = processedTimestamp; }

    @Override
    public String toString() {
        return "OutputData{" +
            "id=" + id +
            ", name='" + name + '\\'' +
            ", processedValue=" + processedValue +
            ", processedTimestamp=" + processedTimestamp +
            '}';
    }
}
''',
        "DataProcessingItemProcessor.java": '''package com.example.batch.processor;

import org.springframework.batch.item.ItemProcessor;
import org.springframework.stereotype.Component;
import com.example.batch.model.InputData;
import com.example.batch.model.OutputData;

@Component
public class DataProcessingItemProcessor implements ItemProcessor<InputData, OutputData> {

    @Override
    public OutputData process(InputData input) throws Exception {
        if (input == null) {
            return null;
        }

        Integer processedValue = input.getValue() * 2;

        OutputData output = new OutputData(
            input.getId(),
            input.getName().toUpperCase(),
            processedValue
        );

        System.out.println("Processing: " + input + " -> " + output);
        return output;
    }
}
''',
        "DatabaseItemWriter.java": '''package com.example.batch.writer;

import org.springframework.batch.item.Chunk;
import org.springframework.batch.item.ItemWriter;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;
import com.example.batch.model.OutputData;
import java.util.List;

@Component
public class DatabaseItemWriter implements ItemWriter<OutputData> {

    private final JdbcTemplate jdbcTemplate;

    public DatabaseItemWriter(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    @Override
    public void write(Chunk<? extends OutputData> chunk) throws Exception {
        String sql = "INSERT INTO output_data (id, name, processed_value, processed_timestamp) " +
                     "VALUES (?, ?, ?, ?)";

        for (OutputData output : chunk) {
            jdbcTemplate.update(sql,
                output.getId(),
                output.getName(),
                output.getProcessedValue(),
                output.getProcessedTimestamp()
            );
        }

        System.out.println("Wrote " + chunk.size() + " items");
    }
}
''',
        "JobCompletionNotificationListener.java": '''package com.example.batch.listener;

import org.springframework.batch.core.BatchStatus;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.listener.JobExecutionListenerSupport;
import org.springframework.stereotype.Component;

@Component
public class JobCompletionNotificationListener extends JobExecutionListenerSupport {

    @Override
    public void afterJob(JobExecution jobExecution) {
        if (jobExecution.getStatus() == BatchStatus.COMPLETED) {
            System.out.println("!!! JOB FINISHED! Time to verify results!!!");
        } else if (jobExecution.getStatus() == BatchStatus.FAILED) {
            System.out.println("!!! JOB FAILED! Status: " + jobExecution.getStatus());
            jobExecution.getAllFailureExceptions().forEach(e -> e.printStackTrace());
        }
    }
}
'''
    }


def generate_spring_batch_database_schema() -> Dict[str, str]:
    """Generate database schema for Spring Batch"""
    return {
        "batch_schema.sql": '''-- Spring Batch Schema
CREATE TABLE IF NOT EXISTS batch_job_instance (
    job_instance_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    version BIGINT,
    job_name VARCHAR(100) NOT NULL,
    job_key VARCHAR(32) NOT NULL,
    UNIQUE KEY UK_BATCH_JI_JOBNAME_JOBKEY (job_name, job_key)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS batch_job_execution (
    job_execution_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    version BIGINT,
    job_instance_id BIGINT NOT NULL,
    create_time DATETIME NOT NULL,
    start_time DATETIME,
    end_time DATETIME,
    status VARCHAR(10),
    exit_code VARCHAR(20),
    exit_message VARCHAR(2500),
    last_updated DATETIME,
    FOREIGN KEY (job_instance_id) REFERENCES batch_job_instance(job_instance_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS batch_step_execution (
    step_execution_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    version BIGINT,
    step_name VARCHAR(100) NOT NULL,
    job_execution_id BIGINT NOT NULL,
    create_time DATETIME NOT NULL,
    start_time DATETIME,
    end_time DATETIME,
    status VARCHAR(10),
    commit_count BIGINT,
    read_count BIGINT,
    filter_count BIGINT,
    write_count BIGINT,
    read_skip_count BIGINT,
    write_skip_count BIGINT,
    process_skip_count BIGINT,
    rollback_count BIGINT,
    exit_code VARCHAR(20),
    exit_message VARCHAR(2500),
    last_updated DATETIME,
    FOREIGN KEY (job_execution_id) REFERENCES batch_job_execution(job_execution_id)
) ENGINE=InnoDB;

-- Application Schema
CREATE TABLE IF NOT EXISTS input_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    value INT NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS output_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    processed_value INT NOT NULL,
    processed_timestamp BIGINT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
'''
    }


def generate_spring_batch(framework: str, language: str, job_name: str = None) -> Dict[str, str]:
    """Generate complete Spring Batch infrastructure"""
    output = {}

    job_name = job_name or "default_job"

    # Configuration
    output.update(generate_spring_batch_job_config())

    # Database schema
    output.update(generate_spring_batch_database_schema())

    # Application properties
    output["application.properties"] = f'''spring.application.name=batch-job-processor
spring.batch.job.enabled=false
spring.datasource.url=jdbc:mysql://localhost:3306/batch_db
spring.datasource.username=root
spring.datasource.password=
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.show-sql=false
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.MySQL8Dialect

# Batch configuration
spring.batch.jdbc.initialize-database=always
spring.batch.jdbc.table-prefix=batch_

# Logging
logging.level.org.springframework.batch=DEBUG
logging.level.com.example.batch=INFO
'''

    return output
